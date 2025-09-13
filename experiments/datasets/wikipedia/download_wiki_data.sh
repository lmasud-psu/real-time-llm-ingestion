export KAGGLE_USERNAME=XXXXX
export KAGGLE_KEY=XXXXX

curl -L -o english-wikipedia-people-dataset.zip \
  -u "${KAGGLE_USERNAME}:${KAGGLE_KEY}" \
  "https://www.kaggle.com/api/v1/datasets/download/wikimedia-foundation/english-wikipedia-people-dataset"

# Unzip into this directory
unzip -o english-wikipedia-people-dataset.zip -d .
