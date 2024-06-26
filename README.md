# Arxiv Consultant
---
> A consultant that can understand user queries from a set of papers from arXiv dataset related to a domain.
---

## Table of Contents
* [In Action](#in-action)
* [Steps to Run the Project](#steps-to-run-the-project)
* [Dataset](#dataset)
* [System Design](#system-design)
* [Flow Chart](#flow-chart)
* [Conclusion](#conclusion)

## In Action

https://github.com/shruthipv96/ArxivConsultant/assets/32814013/aee15af0-c5d9-4545-ba91-04b33d378579

Detailed report of the project is available at [here](https://github.com/shruthipv96/ArxivConsultant/blob/main/ArxivConsultant_Guide.pdf).

## Steps to Run the Project
There are three ways to run the project.
### 1. GUI (‘gui’ folder)
- Open the ‘gui’ folder in Visual Studio Code
- Ensure OpenAI Account and API Keys:
  - Create an account on OpenAI if you don't have one.
  - Make sure you have enough credits to use the gpt model.
  - Obtain your API keys and save them in a file named Open_AI_Key.txt
- Run the Main Application File:
  - Locate the **main.py** file in the project directory.
  - Execute the **main.py** file to start the chatbot gui. This file contains the initial flow of the code and will set everything in motion.

![image](https://github.com/shruthipv96/ArxivConsultant/assets/32814013/59edc28d-33bd-4b6f-8308-930642027848)

### 2. Terminal (‘gui’ folder)
- Open the ‘gui’ folder in Visual Studio Code
- Ensure OpenAI Account and API Keys:
  - Create an account on OpenAI if you don't have one.
  - Make sure you have enough credits to use the gpt model.
  - Obtain your API keys and save them in a file named Open_AI_Key.txt
- Run the Terminal Application File:
  - Locate the **arxiv_consultant.py** file in the project directory.
  - Execute the **arxiv_consultant.py** file to start the chatbot terminal. 

![image](https://github.com/shruthipv96/ArxivConsultant/assets/32814013/9993d788-56ef-4583-97a1-2a0739efe81d)

### 3. Notebook (‘notebook’ folder)
- Open the Jupyter Notebook: Ensure you have the Jupyter Notebook for this project open and run all the cells for the first time after launch.
- Navigate to the Playground Section: Scroll to the end of the notebook until you find the section titled "Playground" or jump from the Table of Contents.
- Experiment the consultant by following the instructions.

![image](https://github.com/shruthipv96/ArxivConsultant/assets/32814013/735652af-1069-4f37-80ae-3b8d1a022d51)

#### Note: 
* **Installation:** Run `pip install -r requirements.txt` to install all the dependencies.
* Since we are using online LLM models, sometimes response might be not as expected, so reset and try again.

## Dataset
* The dataset is downloaded dynamically with the help of user inputs.
  
## System Design

![image](https://github.com/shruthipv96/ArxivConsultant/assets/32814013/4f7dcc5b-6ca9-4360-a384-0ffafacc1cd5)

| Layer | Summary |
|-------|---------|
| Build tools	| This layer enables flexible querying and summarization of academic papers fetched dynamically from Arxiv based on user-specified search queries. Adjustments can be made for different functionalities or enhancements as needed. |
| Object Retreiver | This layer facilitates the retrieval of relevant objects, node processing, and mapping to tools. It integrates with query engines, postprocessors, and other components to enhance querying capabilities effectively. |
| Generate query response |	This layer sets up a react agent that efficiently fetches objects from Arxiv papers based on pre-defined tools and criteria, ensuring optimal search result reranking and retrieval. |

## Flow Chart
### System :
![image](https://github.com/shruthipv96/ArxivConsultant/assets/32814013/231e197d-497f-437f-bee3-d12897137023)

### GUI :
![image](https://github.com/shruthipv96/ArxivConsultant/assets/32814013/c2312b35-4880-4a7f-8892-6590e832e746)

## Conclusion
With the Arxiv consultant, user can do efficient search, understanding and comparison of the papers related to the interested field.

### Key points
* Breaking down functionality into modular components like ObjectRetriever, ArxivBuilder, and ReActAgent allows for easier maintenance, testing, and scalability of the system.
* Employing threading for tasks like building agents and handling user interactions ensures the GUI remains responsive during potentially long-running operations.
* Designing user interfaces (UI) with clear input fields, buttons, and message displays enhances usability and user experience.
* Integrating external libraries (SentenceTransformer, ArxivBuilder) and APIs (e.g., OpenAI for language models) expands functionality and leverages specialized tools for tasks like semantic similarity and document retrieval.
* Designing coherent interaction flows between CLI (ArxivConsultant) and GUI (ConsultantUI) versions of the application ensures consistency and flexibility in how users interact with the system.

### Areas of Improvement
* Optimizing the performance of various operations, such as retrieving and processing papers from Arxiv, can be challenging, especially with large datasets.
* Designing the system to be easily scalable and extensible for future features and larger datasets can be difficult.
* Feedback assistant could be improved to better understand the user satisfaction.
* Managing long-running operations, such as fetching and processing papers, without blocking the user interface requires careful design.

## Contact
Created by [Shruthip Venkatesh](https://github.com/shruthipv96) - feel free to contact me!
