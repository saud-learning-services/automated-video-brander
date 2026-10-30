#!/bin/zsh
# Double-click in Finder to start the automated brander in a Terminal window.
# Leave the window open: it runs the brander at 09:10 and 16:00 every day.
cd "$(dirname "$0")"
ENV_NAME=automated-editor-py315

for c in "$HOME/miniforge3" "$HOME/miniconda3" "$HOME/anaconda3" \
         /opt/homebrew/Caskroom/miniforge/base /opt/miniconda3 /opt/anaconda3; do
  if [ -f "$c/etc/profile.d/conda.sh" ]; then
    source "$c/etc/profile.d/conda.sh"
    break
  fi
done

if ! conda activate "$ENV_NAME" 2>/dev/null; then
  echo "Could not find the conda environment '$ENV_NAME'. See README > Environment."
  echo "Press Return to close."
  read
  exit 1
fi

python launcher.py

echo "Brander stopped. Press Return to close."
read
