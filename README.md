# AI Tools for 2025 Interim Surveillance Review

## Overview
This project utilizes AI tools for the 2025 interim surveillance review. The project is structured into various sections, each focusing on a specific aspect of the setup and usage of these tools.

## Environment Setup

1. **Create a New Virtual Environment:**
   - Set up a new virtual environment for this project.
   - Activate the environment and install required packages using:
     ```
     pip install -r requirements.txt
     ```

2. **Download Data:**
   - Data for this project should be downloaded and stored in the same root folder as this repository.
   - Use the following command to download the data (link will be provided soon):
     ```
     wget [link pending]
     ```
   - You are also advised to have a openai_key.json file udner [root_folder]/key/openai_key.json     
     ```
        {
           "ISR": {
            "API_KEY": "xxxxxxxxx"
            }
        }
     ```

## Folder Structure

- **`libs` Directory:**
  - Contains a collection of utility functions designed for the OpenAI assistant.

- **`notebooks` Directory:**
  - Includes various testing files for different functions, allowing for experimentation and validation of the tools.

- **`src` Directory:**
  - Hosts code snippets and scripts necessary to complete the required tasks for the review.

## To-Do List

- [ ] Task 1: Extract all risks, likelihood and policy responses from AIVs; clean them up  -- Chengyu
- [ ] Task 2: Process/clean raw AIV info, remove elements like authorities' views ; appendex ; data tables etc; (Di has done some work before, need to be tweaked)
- [ ] Task 3: Design a step by step process to use GPT to answer ISR questions
- [ ] Task 4: Design a strategy to categorize generate responses (in the end they need to be some kind of charts of summaries)

## Contact
- chuang@imf.org
