---
language:
- en
multilinguality:
- monolingual
size_categories:
- 100K<n<1M
task_categories:
- feature-extraction
- sentence-similarity
pretty_name: CC News
tags:
- sentence-transformers
dataset_info:
  config_name: pair
  features:
  - name: title
    dtype: string
  - name: article
    dtype: string
  splits:
  - name: train
    num_bytes: 1529462734
    num_examples: 614664
  download_size: 960719023
  dataset_size: 1529462734
configs:
- config_name: pair
  data_files:
  - split: train
    path: pair/train-*
---

# Dataset Card for CC News

This dataset is a collection of title-article pairs collected from CC News. See [cc_news](https://huggingface.co/datasets/vblagoje/cc_news) for additional information.
This dataset can be used directly with Sentence Transformers to train embedding models.

## Dataset Subsets

### `pair` subset

* Columns: "title", "article"
* Column types: `str`, `str`
* Examples:
    ```python
    {
      'title': 'Tennessee joins states urging court to reinstate travel ban',
      'article': 'NASHVILLE, Tenn. (AP) – Tennessee is joining more than a dozen other states in urging an appeals court to reinstate President Donald Trump’s revised travel ban.\nState Senate Majority Leader Mark Norris, a Collierville Republican considering a bid for governor next year, lauded Attorney General Herbert Slatery’s office for filing a brief with the 9th U.S. Circuit Court of Appeals in San Francisco.\nThe states argue the ban falls within the president’s authority to block foreigners from the U.S. They also reject the argument that it targets Muslims.\nNorris last year sponsored legislation to allow the General Assembly to hire its own attorneys to file a legal challenge seeking to halt the federal refugee resettlement program in Tennessee after Slatery and Gov. Bill Haslam declined to sue over the issue.',
    }
    ```
* Collection strategy: Reading the CC News dataset from [embedding-training-data](https://huggingface.co/datasets/sentence-transformers/embedding-training-data).
* Deduplified: No