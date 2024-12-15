# -*- coding: utf-8 -*-
"""Question Answering System with Structured Data.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/16Qfx5mVCTyB9mE-sbOvBdIoq_1b2j1mK
"""

# # Question Answering

# Idea-1 SQL-based model
# SQL-based: Develop Text-to-Sql generation system with Google Gemini Pro LLM (Colab-based code) (UI-based code will be done if goes with this)

# Idea-2 RAG based model with CSV data
# RAG: Build Chatbot with CSV data (RAG) with Open source Mistral LLM and LangChain framework (Colab-based code) (UI-based code will be done if goes with this)

# Idea-3 pre-train model on your own data TAPAS model (UI-based code will be done if goes with this)

# Dataset: https://www.kaggle.com/datasets/prathammalvia/imdb-sqlite-dataset

# Idea-1 AgenticAI and SQL-based model
# SQL-based: Develop Text-to-Sql generation system with Google Gemini Pro LLM (Colab-based code)

!pip install -q -U langchain==0.1.2
!pip install -q -U google-generativeai==0.5.2
!pip install -q -U langchain-google-genai==1.0.3

from google.colab import userdata
GOOGLE_API_KEY = userdata.get('GEMINI_KEY')

from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri("sqlite:////content/movies.sqlite")
print(db.dialect)
print(db.get_usable_table_names())

print("Q1: ")
db.run("SELECT * FROM directors LIMIT 1;")
# columns=['name', 'id', 'gender', 'uid', 'department']

print("Q2: ")
db.run("SELECT * FROM movies LIMIT 1;")
# columns=['id', 'original_title', 'budget', 'popularity', 'release_date',
# 'revenue', 'title', 'vote_average', 'vote_count', 'overview', 'tagline',
# 'uid', 'director_id' ]

import re
from langchain.chains import create_sql_query_chain
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=GOOGLE_API_KEY, convert_system_message_to_human=True, temperature=0.0)
chain = create_sql_query_chain(llm, db)
response = chain.invoke({"question": "How many directors are men"})
response

# Generate regex pattern to remove prefix and suffix
regex_pattern = r'^```sql\n|\n```$'

# Remove prefix and suffix using regex to get proper SQL query
modified_response = re.sub(regex_pattern, '', response)
print(modified_response)

db.run(modified_response)

chain.get_prompts()[0].pretty_print()

from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough

answer_prompt = PromptTemplate.from_template(
"""Given the following user question, corresponding SQL query, and SQL result, answer the user question.

Question: {question}
{query}
SQL Result: {result}
Answer: """
)

answer = answer_prompt | llm | StrOutputParser()
chain = (
    RunnablePassthrough.assign(query=write_query).assign(
        result=itemgetter("query") | execute_query
    )
    | answer
)

chain.invoke({"question": "How many directors are men"})

chain.invoke({'question': "How many movie relaesed in year 2010? Which movie has the most rating and who directed in 2010?"})

chain.invoke({'question': "List all the total movie of year 2010."})

chain.invoke({'question': "List the top 5 movie of 2010 with highest rating?"})

chain.invoke({'question': "Which directors directed 5 highest rated movies of year 2010 (also add name and rating of the movie)?"})







# Idea-2 RAG based model with CSV data
# RAG: Build Chatbot (RAG) on your local Laptop using Open Source Mistral LLM and LangChain framework (Colab-based code)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3

db = '/content/movies.sqlite'
sqliteConnection = sqlite3.connect(db)
cur = sqliteConnection.cursor()

# Get all the data about movies
query='SELECT * FROM movies'
cur.execute(query)
movies = cur.fetchall()

# Displaying the movies data
movies[:3]

query='SELECT * FROM directors'
cur.execute(query)
directors=cur.fetchall()

# Displaying the directors data
directors[:3]

# Creating a movies DataFrame
movies=pd.DataFrame(movies, columns=['id', 'original_title', 'budget', 'popularity', 'release_date',
'revenue', 'title', 'vote_average', 'vote_count', 'overview', 'tagline',
'uid', 'director_id' ])

# Displaying the movies DataFrame
movies.head()

movies.columns

import os
os.mkdir('data')

movies.to_csv("data/movies.csv", index=False)

# Creating a directors DataFrame
directors=pd.DataFrame(directors, columns=['name', 'id', 'gender', 'uid', 'department'])

# Displaying the directors DataFrame
directors.head()

directors.columns

directors.to_csv("data/directors.csv", index=False)





# Huggingface libraries to run LLM.
!pip install -q -U transformers==4.40.2
!pip install -q -U accelerate==0.30.1
!pip install -q -U bitsandbytes==0.43.1
!pip install -q -U huggingface_hub==0.23.0

#LangChain related libraries
!pip install -q -U langchain==0.1.2

#Open-source pure-python PDF library capable of splitting, merging, cropping,
#and transforming the pages of PDF files
!pip install -q -U pypdf==4.2.0

#Python framework for state-of-the-art sentence, text and image embeddings.
!pip install -q -U sentence-transformers==2.7.0

# FAISS Vector Databses specific Libraries
!pip install -q -U faiss-gpu==1.7.2

from huggingface_hub import login
from google.colab import userdata

login(token=userdata.get('HF_KEY'))

#from typing import List
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer, AutoConfig, BitsAndBytesConfig
import torch
from langchain.llms import HuggingFacePipeline

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import HuggingFaceHub
from langchain.vectorstores import Chroma
from langchain.chains import ConversationalRetrievalChain

import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'

print("Device:", device)
if device == 'cuda':
    print(torch.cuda.get_device_name(0))

origin_model_path = "mistralai/Mistral-7B-Instruct-v0.1"
model_path = "filipealmeida/Mistral-7B-Instruct-v0.1-sharded"
bnb_config = BitsAndBytesConfig \
              (
                load_in_4bit=True,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=torch.bfloat16,
              )
model = AutoModelForCausalLM.from_pretrained (model_path, trust_remote_code=True,
                                              quantization_config=bnb_config,
                                              device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(origin_model_path)

text_generation_pipeline = transformers.pipeline(
    model=model,
    tokenizer=tokenizer,
    task="text-generation",
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.eos_token_id,
    repetition_penalty=1.1,
    return_full_text=False,
    max_new_tokens=300,
    temperature = 0.3,
    do_sample=True,
)
mistral_llm = HuggingFacePipeline(pipeline=text_generation_pipeline)



import locale
locale.getpreferredencoding = lambda: "UTF-8"

from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders import DirectoryLoader
# loader = DirectoryLoader('./data', glob='**/*.csv', loader_cls=CSVLoader)
loader = CSVLoader('./data/movies.csv')
data = loader.load()

# Split the documents into smaller chunks
#separator=""
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
chunked_docs  = text_splitter.split_documents(data)

# Using HuggingFace embeddings
embeddings = HuggingFaceEmbeddings()

from langchain.vectorstores import FAISS
db = FAISS.from_documents(chunked_docs,
                          HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2'))


# Connect query to FAISS index using a retriever
retriever = db.as_retriever(
    search_type="similarity",
    search_kwargs={'k': 4}
)

# Create the Conversational Retrieval Chain
qa_chain = ConversationalRetrievalChain.from_llm(mistral_llm, retriever,return_source_documents=True)

import sys
chat_history = []

while True:
  query = input('Prompt: ')
  # Ask question related CSV file like Which country has highest green gas?
  if query.lower().strip()=="exit":
    break
  result = qa_chain.invoke({'question': query, 'chat_history': chat_history})

  print('Answer: ' + result['answer'] + '\n')
  chat_history.append((query, result['answer']))

chat_history

while True:
  query = input('Prompt: ')
  # Ask question related CSV file like Which country has highest green gas?
  if query.lower().strip()=="exit":
    break
  result = qa_chain.invoke({'question': query, 'chat_history': chat_history})

  print('Answer: ' + result['answer'] + '\n')
  chat_history.append((query, result['answer']))

chat_history





# Idea-3 pre-train model on your own data TAPAS model

# paper: https://aclanthology.org/2020.acl-main.398.pdf

# Refer to learn more: https://colab.research.google.com/github/NielsRogge/Transformers-Tutorials/blob/master/TAPAS/Fine_tuning_TapasForQuestionAnswering_on_SQA.ipynb



import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import sqlite3

db = '/content/movies.sqlite'
sqliteConnection = sqlite3.connect(db)
cur = sqliteConnection.cursor()

# Get all the data about movies
query='SELECT * FROM movies'
cur.execute(query)
movies = cur.fetchall()

# Displaying the movies data
movies[:3]

query='SELECT * FROM directors'
cur.execute(query)
directors=cur.fetchall()

# Displaying the directors data
directors[:3]

# Creating a movies DataFrame
movies=pd.DataFrame(movies, columns=['id', 'original_title', 'budget', 'popularity', 'release_date',
'revenue', 'title', 'vote_average', 'vote_count', 'overview', 'tagline',
'uid', 'director_id' ])

# Displaying the movies DataFrame
movies.head()

movies.columns

import os
os.mkdir('data')

movies.to_csv("data/movies.csv", index=False)

# Creating a directors DataFrame
directors=pd.DataFrame(directors, columns=['name', 'id', 'gender', 'uid', 'department'])

# Displaying the directors DataFrame
directors.head()

directors.columns

directors.to_csv("data/directors.csv", index=False)





import torch
device = 'cuda' if torch.cuda.is_available() else 'cpu'

print("Device:", device)
if device == 'cuda':
    print(torch.cuda.get_device_name(0))
CUDA = torch.version.cuda
print(torch.version.cuda)

!pip install transformers

# !pip install torch-scatter -f https://pytorch-geometric.com/whl/torch-1.6.0+${CUDA}.html

from transformers import TapasTokenizer, TapasForQuestionAnswering
import pandas as pd

# Define the table
data = pd.read_csv('./data/movies.csv')
data.head()

# new_data = data.to_dict('list')
# pprint(new_data)
for i in data.columns:
  data[i] = data[i].astype('str')

queries = ["When was Avatar movie released?",
           "What is the budget of Spectre?",
           "What is the vote average of The Dark Knight Rises?",
           "What is the tagline of Pirates of the Caribbean: At World's End?"]

# # Define the questions
# queries = ["When was Inception movie released?",
#            "Which movie has low rating than Inception released around same time?",
#            "What is the ratings of Final Destination?",
#            "What is the ratings of Identity?",
#            "What is the tagline of Inception?"]
# queries

# # Define the table
# data = {'Cities': ["Paris, France", "London, England", "Lyon, France"], 'Inhabitants': ["2.161", "8.982", "0.513"]}

# # Define the questions
# queries = ["Which city has most inhabitants?", "What is the average number of inhabitants?", "How many French cities are in the list?", "How many inhabitants live in French cities?"]

def load_model_and_tokenizer():
  """
    Load
  """
  # Load pretrained tokenizer: TAPAS finetuned on WikiTable Questions
  tokenizer = TapasTokenizer.from_pretrained("google/tapas-base-finetuned-wtq")

  # Load pretrained model: TAPAS finetuned on WikiTable Questions
  model = TapasForQuestionAnswering.from_pretrained("google/tapas-base-finetuned-wtq")

  # Return tokenizer and model
  return tokenizer, model

def prepare_inputs(data, queries, tokenizer):
  """
    Convert dictionary into data frame and tokenize inputs given queries.
  """
  # Prepare inputs
  table = pd.DataFrame.from_dict(data)
  # table = data
  inputs = tokenizer(table=table, queries=queries, padding='max_length', truncation=True,  return_tensors="pt")

  # Return things
  return table, inputs

def generate_predictions(inputs, model, tokenizer):
  """
    Generate predictions for some tokenized input.
  """
  # Generate model results
  outputs = model(**inputs)

  # Convert logit outputs into predictions for table cells and aggregation operators
  predicted_table_cell_coords, predicted_aggregation_operators = tokenizer.convert_logits_to_predictions(
          inputs,
          outputs.logits.detach(),
          outputs.logits_aggregation.detach()
  )

  # Return values
  return predicted_table_cell_coords, predicted_aggregation_operators

def postprocess_predictions(predicted_aggregation_operators, predicted_table_cell_coords, table):
  """
    Compute the predicted operation and nicely structure the answers.
  """
  # Process predicted aggregation operators
  aggregation_operators = {0: "NONE", 1: "SUM", 2: "AVERAGE", 3:"COUNT"}
  aggregation_predictions_string = [aggregation_operators[x] for x in predicted_aggregation_operators]

  # Process predicted table cell coordinates
  answers = []
  for coordinates in predicted_table_cell_coords:
    if len(coordinates) == 1:
      # 1 cell
      answers.append(table.iat[coordinates[0]])
    else:
      # > 1 cell
      cell_values = []
      for coordinate in coordinates:
        cell_values.append(table.iat[coordinate])
      answers.append(", ".join(cell_values))

  # Return values
  return aggregation_predictions_string, answers

def show_answers(queries, answers, aggregation_predictions_string):
  """
    Visualize the postprocessed answers.
  """
  for query, answer, predicted_agg in zip(queries, answers, aggregation_predictions_string):
    print(query)
    if predicted_agg == "NONE":
      print("Predicted answer: " + answer)
    else:
      print("Predicted answer: " + predicted_agg + " > " + answer)

def run_tapas(data):
  """
    Invoke the TAPAS model.
  """
  tokenizer, model = load_model_and_tokenizer()
  table, inputs = prepare_inputs(data, queries, tokenizer)
  predicted_table_cell_coords, predicted_aggregation_operators = generate_predictions(inputs, model, tokenizer)
  aggregation_predictions_string, answers = postprocess_predictions(predicted_aggregation_operators, predicted_table_cell_coords, table)
  show_answers(queries, answers, aggregation_predictions_string)

run_tapas(data[:4].to_dict())
