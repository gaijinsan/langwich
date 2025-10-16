#!/bin/bash

# --- CONFIGURATION ---
# Get the name of the current project directory (e.g., 'my_python_app')
PROJECT_NAME=$(basename "$(pwd)")

# Determine deployment mode and directory suffix
DEPLOY_MODE=$1
LIVE_DEPLOYMENT_SUFFIX="_live"
DEV_DEPLOYMENT_SUFFIX="_dev"

if [ "$DEPLOY_MODE" == "dev" ]; then
    DEPLOYMENT_SUFFIX="$DEV_DEPLOYMENT_SUFFIX"
    SHARED="shared_dev"
elif [ "$DEPLOY_MODE" == "live" ]; then
    DEPLOYMENT_SUFFIX="$LIVE_DEPLOYMENT_SUFFIX"
    SHARED="shared"
else
    echo "Usage: $0 [dev|live]"
    echo "  'dev'  - Deploy to a development environment (for testing)"
    echo "  'live' - Deploy to a live production environment"
    exit 1
fi

# Define the root directory for all deployment artifacts.
DEPLOY_ROOT="../${PROJECT_NAME}${DEPLOYMENT_SUFFIX}"

# Define directories that contain persistent, application-generated data.
# These directories will be excluded from code copying and symlinked from a 'shared' location.
USER_DATA=("backups" "text_sentences" "text_words" "texts" "words" "metadata.json")

# Define structural directories within DEPLOY_ROOT
RELEASES_DIR="$DEPLOY_ROOT/releases"
SHARED_DIR="$DEPLOY_ROOT/$SHARED"
CURRENT_SYMLINK="$DEPLOY_ROOT/langwich"

# Create a unique, timestamped release directory for this new code version
TIMESTAMP=$(date +%Y%m%d%H%M%S)
RELEASE_DIR="$RELEASES_DIR/$TIMESTAMP"

# Global arrays to hold generated rsync rules from .gitignore
# THESE MUST BE ARRAYS to correctly preserve quoting for rsync arguments.
DEV_INCLUDES=()
DEV_EXCLUDES=()

# --- CORE FUNCTIONS ---

# Function to read .gitignore and convert its patterns into rsync --exclude arguments.
# Handles negation (!) by converting them into --include rules.
generate_gitignore_excludes() {
    echo "Generating rsync exclusions/inclusions from .gitignore..."
    if [ -f .gitignore ]; then
        while IFS= read -r LINE; do
            # 1. Clean line: strip Windows carriage returns (\r) and remove leading/trailing whitespace
            CLEAN_LINE=$(echo "$LINE" | tr -d '\r' | xargs)

            # Skip empty lines and comments, and lines that become empty after cleaning
            if [[ -n "$CLEAN_LINE" && ! "$CLEAN_LINE" =~ ^# ]]; then

                # Check for negation (re-inclusion)
                if [[ "$CLEAN_LINE" =~ ^! ]]; then
                    # Remove the leading '!' using Bash substring manipulation
                    INCLUDE_PATTERN="${CLEAN_LINE#!}"

                    # Process Git's recursive wildcard (**) for rsync compatibility
                    # Remove leading '**/', allowing rsync's unanchored pattern to handle recursion.
                    if [[ "$INCLUDE_PATTERN" =~ ^\*\*\/ ]]; then
                        INCLUDE_PATTERN="${INCLUDE_PATTERN#\*\*/}"
                    fi
                    DEV_INCLUDES+=("--include='$INCLUDE_PATTERN'")
                else
                    # Standard exclusion
                    EXCLUDE_PATTERN="$CLEAN_LINE"

                    # Process Git's recursive wildcard (**) for rsync compatibility
                    if [[ "$EXCLUDE_PATTERN" =~ ^\*\*\/ ]]; then
                        EXCLUDE_PATTERN="${EXCLUDE_PATTERN#\*\*/}"
                    fi
                    DEV_EXCLUDES+=("--exclude=$EXCLUDE_PATTERN")
                fi
            fi
        done < .gitignore
    else
        echo "Warning: .gitignore file not found. Applying minimum safe exclusions."
        # If no .gitignore exists, we must re-add the minimum safe exclusions manually
        DEV_EXCLUDES+=("--exclude=*.pyc")
        DEV_EXCLUDES+=("--exclude=*/__pycache__")
    fi
}

# Sets up the shared directory structure and handles initial copy of shared files
setup_shared_dirs() {
    echo "Ensuring shared data directories and files exist..."
    for ARTIFACT in "${USER_DATA[@]}"; do
        SHARED_PATH="$SHARED_DIR/$ARTIFACT"
        SHARED_PARENT=$(dirname "$SHARED_PATH")

        # 1. Ensure the shared parent directory exists
        mkdir -p "$SHARED_PARENT"

        if [ -d "$ARTIFACT" ]; then
            # If it's a directory (like 'data' or 'logs'), ensure the shared directory exists
            mkdir -p "$SHARED_PATH"
        elif [ -f "$ARTIFACT" ]; then
            # If it's a file (like 'metadata.json'), copy it to shared ONLY if it doesn't exist in shared yet.
            # This ensures the first deployment uses the version from the repo.
            if [ ! -f "$SHARED_PATH" ]; then
                echo "-> Copying initial file artifact '$ARTIFACT' to shared location."
                cp "$ARTIFACT" "$SHARED_PATH"
            fi
        fi
    done
}

# Symlinks the shared data directories and files into the new release
symlink_shared_dirs() {
    echo "Symlinking persistent data artifacts into release $TIMESTAMP..."
    for ARTIFACT in "${USER_DATA[@]}"; do
        # 1. Remove the artifact if it was accidentally copied with the code
        if [ -e "$RELEASE_DIR/$ARTIFACT" ]; then
            rm -rf "$RELEASE_DIR/$ARTIFACT"
        fi

        RELATIVE_PATH="../../$SHARED/$ARTIFACT"

        # 2. Create the symlink from the release to the shared location
        ln -s "$RELATIVE_PATH" "$RELEASE_DIR/$ARTIFACT"
        #ln -s "$SHARED_DIR/$ARTIFACT" "$RELEASE_DIR/$ARTIFACT"
    done
}

# --- DEPLOYMENT STEPS ---

echo "--- Starting Deployment for $PROJECT_NAME (Release: $TIMESTAMP) ---"

# 0. Generate exclusions based on .gitignore
generate_gitignore_excludes

# 1. Setup root and shared directories
mkdir -p "$RELEASES_DIR"
setup_shared_dirs

# 2. Prepare persistent data exclusions
echo "Preparing exclusions for persistent data artifacts..."
EXCLUDE_ARGS=()
for ARTIFACT in "${USER_DATA[@]}"; do
    # Persistent data directories/files must always be excluded from the copy
    EXCLUDE_ARGS+=("--exclude=/$ARTIFACT")
done

# 3. Copy essential project files to the new RELEASE_DIR
# IMPORTANT: The order of flags matters for rsync.
#     1. Includes ($DEV_INCLUDES) take precedence over
#     2. Excludes ($DEV_EXCLUDES).
#     3. Hardcoded exclusions (like /.git)
#     4. Data exclusions ($EXCLUDE_ARGS)
echo "Copying essential project files..."

rsync -av --progress \
    "${DEV_INCLUDES[@]}" \
    "${DEV_EXCLUDES[@]}" \
    --exclude=/.git \
    --exclude=/.gitignore \
    --exclude=/tests \
    --exclude=/pytest.ini \
    --exclude=/deploy.sh \
    --exclude=/requirements-dev.txt \
    --exclude=/pyproject.toml \
    "${EXCLUDE_ARGS[@]}" \
    . "$RELEASE_DIR"

rsync -av --progress ./pyproject.toml "$DEPLOY_ROOT"
# 4. Remove all .gitkeep files from the clean release copy
echo "Removing all .gitkeep files from the new release..."
find "$RELEASE_DIR" -name ".gitkeep" -delete

# 4.5 If deploy to dev, write a .env file with development settings
if [ "$DEPLOY_MODE" == "dev" ]; then
    echo $DEPLOY_MODE > "$RELEASE_DIR/.app_env_mode"
fi

# 5. Create symlinks for persistent data files and directories
symlink_shared_dirs

# 6. Switch the 'current' symlink to point to the new release
echo "Switching active deployment to the new release: $TIMESTAMP"
rm -f "$CURRENT_SYMLINK"
ln -s "$RELEASE_DIR" "$CURRENT_SYMLINK"

echo "--- Deployment Complete! ---"
echo "Active version is now running from: $CURRENT_SYMLINK"
echo "Persistent data is stored in: $SHARED_DIR"
echo ""

# 7. Display next steps for running the application
echo "=========================================================="
echo "          NEXT STEPS: Running the Deployed App"
echo "=========================================================="
echo "Deployment structure:"
echo "  $DEPLOY_ROOT/"
echo "  ├── langwich -> releases/$TIMESTAMP"
echo "  ├── releases/"
echo "  └── $SHARED/ (contains persistent data: data, logs, etc.)"
echo ""
echo "You must set up a clean virtual environment in the new release folder:"
echo ""
echo "0. Change directory:"
echo "   cd $CURRENT_SYMLINK"
echo ""
echo "1. Select the python version:"
echo "   pyenv local 3.13.5"
echo ""
echo "2. Create a new virtual environment (named 'venv' here):"
echo "   python -m venv venv"
echo ""
echo "3. Activate the new environment:"
echo "   source venv/bin/activate"
echo ""
echo "4. Install dependencies:"
echo "   pip install -r requirements.txt"
echo ""
echo "5. Ensure xclip or similar is installed so that pyperclip will work:"
echo "   sudo apt update"
echo "   sudo apt install xclip"
echo ""
echo "6. Install the local project as a package (REQUIRED for python -m to work):"
echo "   cd .."
echo "   pip install -e ."
echo "   # NOTE: This step requires a 'setup.py' or 'pyproject.toml' file in the current directory."
echo "   # If you see an error, your project is missing a Python packaging definition."
echo ""
echo "7. Run the application using the correct module and entry point:"
echo "   python -m $PROJECT_NAME.<entry_point>"
echo "   (Example: If your project is named 'langapp' and the entry module is 'cli', run: python -m langapp.cli)"
