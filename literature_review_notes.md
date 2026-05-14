# Literature Review Notes

## Purpose
This note collects concrete prior work that is close to the current project so the paper draft does not rely on unsupported novelty claims.

## Core References

### 1. OpenTag: Open Attribute Value Extraction from Product Profiles
- Authors: Guineng Zheng, Subhabrata Mukherjee, Xin Luna Dong, Feifei Li
- Year: 2018
- Venue: KDD 2018
- URL: https://arxiv.org/abs/1806.01264

What it does:
- Extracts missing attribute values from product titles and descriptions
- Frames the problem as sequence tagging
- Uses BiLSTM-CRF with attention and active learning

Why it matters here:
- It is a strong early product-attribute extraction reference
- It shows that product attribute extraction is already a real research problem

Why it does not solve our problem directly:
- It focuses on attribute value extraction from product profiles, not short user queries
- It does not model attribute priority order
- It does not model synonym-key preference order

### 2. BERT for Joint Intent Classification and Slot Filling
- Authors: Qian Chen, Zhu Zhuo, Wen Wang
- Year: 2019
- URL: https://arxiv.org/abs/1902.10909

What it does:
- Jointly models intent classification and slot filling
- Shows that pretrained language models improve structured NLU tasks

Why it matters here:
- It is a strong reference for query understanding and slot-style extraction
- It supports the idea that query parsing should be treated as structured prediction

Why it does not solve our problem directly:
- It focuses on classical intent-and-slot benchmarks
- It does not address product attribute extraction in industrial search
- It does not rank extracted attributes by importance

### 3. Explicit Attribute Extraction in e-Commerce Search
- Authors: Robyn Loughnane, Jiaxin Liu, Zhilin Chen, Zhiqi Wang, Joseph Giroux, Tianchuan Du, Benjamin Schroeder, Weiyi Sun
- Year: 2024
- Venue: ECNLP @ LREC-COLING 2024
- URL: https://aclanthology.org/2024.ecnlp-1.13/

What it does:
- Extracts attribute values from search queries in e-commerce search
- Uses weak labels from customer interactions
- Uses transformer-based NER plus two-stage normalization
- Demonstrates real production value in retrieval and ranking

Why it matters here:
- This is one of the closest references to the current project
- It directly supports the importance of attribute extraction from search queries

Why it does not solve our problem directly:
- It focuses on explicit attribute extraction and normalization
- It does not predict the relative priority order of extracted attributes
- It does not model key-synonym ranking for each extracted value

### 4. Using LLMs for the Extraction and Normalization of Product Attribute Values
- Authors: Alexander Brinkmann, Nick Baumann, Christian Bizer
- Year: 2024
- URL: https://arxiv.org/abs/2403.02130

What it does:
- Uses LLMs to extract and normalize product attribute values
- Introduces the WDC-PAVE benchmark
- Studies extraction plus normalization from product offers

Why it matters here:
- It shows current LLM-based attribute extraction work in commerce
- It is useful for discussing structured extraction plus normalization

Why it does not solve our problem directly:
- It operates on product offers, not short search queries
- It focuses on extraction and normalization, not priority ordering
- It does not output ranked attribute importance or ranked key-synonym lists

## What Seems Novel In Our Direction
Based on the references above, the current project seems to combine several dimensions that are usually handled separately:
- attribute extraction from user search queries
- attribute importance ordering
- synonym-key preference ordering
- generation of a nested structured output that captures both forms of ranking

## Safe Novelty Language
Use this language for now:

"To our knowledge, explicit modeling of both attribute priority order and synonym-key priority order for industrial search queries is underexplored. Existing work covers attribute extraction, slot filling, and attribute normalization, but we have not yet found a directly matching formulation that jointly predicts values, attribute order, and key preference order in the same structured output."

## What Still Needs Review
Before any external submission, we should still do a broader literature sweep on:
- entity salience and importance ranking
- keyphrase ranking from short queries
- facet ranking and query facet identification
- structured generation for commerce search
- attribute extraction in marketplace search logs