# Open AI components
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
# Settings
from llama_index.core import Settings

# Setup Open AI Api Key
OPEN_AI_API_KEY =  open("Open_AI_Key.txt", "r").read().strip()
# Create llm model with Open AI API Key
llm = OpenAI(model="gpt-3.5-turbo", api_key=OPEN_AI_API_KEY)
Settings.llm = llm
# Create embedding model
Settings.embed_model = OpenAIEmbedding(
    model="text-embedding-3-small", embed_batch_size=256, api_key=OPEN_AI_API_KEY
)

# Set the path for storing the required data
storage_path='./storage'

# Number of top results to retrieve and rerank
top_n_results = 5