# ----------------------------------------------------------------------
# Import Libraries
# ----------------------------------------------------------------------

# Necessary libraries
import pickle
import os
from pathlib import Path
from tqdm import tqdm
from typing import Optional

# Reader
from llama_index.core.readers import SimpleDirectoryReader

# Core components
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import load_index_from_storage, StorageContext, VectorStoreIndex, SummaryIndex
from llama_index.core.tools import QueryEngineTool, ToolMetadata

# Open AI components
from llama_index.agent.openai import OpenAIAgent

# Global params
from global_params import llm, storage_path

# ----------------------------------------------------------------------
# Builder Classes
# ----------------------------------------------------------------------
class PaperAgentBuilder():
    """
    A class to build an agent with a vector query engine and summary index tool for a single paper in PDF.
    """

    def __init__(self):
        # Initialize the class with a node parser, which is an instance of SentenceSplitter.
        self.node_parser = SentenceSplitter()

    def build_agent_per_doc(self, nodes, paper_name):
        """
        Build an agent for a single document.

        Parameters:
        nodes (list): List of nodes (parsed sentences or segments) from the document.
        paper_name (str): Name of the paper.

        Returns:
        tuple: (agent, summary) where agent is the built agent and summary is the document summary.
        """
        # Define paths for storing vector index and summary
        vector_index_out_path = f"{storage_path}/vector/{paper_name}"
        summary_out_path = f"{storage_path}/summary/{paper_name}_summary.pkl"
        
        # Check if vector index already exists, if not, create and store it
        if not os.path.exists(vector_index_out_path):
            Path(storage_path).mkdir(parents=True, exist_ok=True)
            # Build vector index using the provided nodes
            vector_index = VectorStoreIndex(nodes)
            vector_index.storage_context.persist(persist_dir=vector_index_out_path)
        else:
            # Load the existing vector index from storage
            vector_index = load_index_from_storage(
                StorageContext.from_defaults(persist_dir=vector_index_out_path),
            )

        # Build summary index from the nodes
        summary_index = SummaryIndex(nodes)

        # Define query engines using the indices and the language model (llm)
        vector_query_engine = vector_index.as_query_engine(llm=llm)
        summary_query_engine = summary_index.as_query_engine(
            response_mode="tree_summarize", llm=llm
        )

        # Extract a summary of the document and store it if not already done
        if not os.path.exists(summary_out_path):
            Path(summary_out_path).parent.mkdir(parents=True, exist_ok=True)
            summary = str(
                summary_query_engine.query(
                    "Extract a concise 5-6 lines summary of this document"
                )
            )
            pickle.dump(summary, open(summary_out_path, "wb"))
        else:
            summary = pickle.load(open(summary_out_path, "rb"))

        # Define tools for querying
        query_engine_tools = [
            QueryEngineTool(
                query_engine=vector_query_engine,
                metadata=ToolMetadata(
                    name=f"vector_tool_{paper_name}",
                    description=f"Useful for questions related to specific facts",
                ),
            ),
            QueryEngineTool(
                query_engine=summary_query_engine,
                metadata=ToolMetadata(
                    name=f"summary_tool_{paper_name}",
                    description=f"Useful for summarization questions",
                ),
            ),
        ]

        # Build the agent with the defined tools and a specific system prompt
        agent = OpenAIAgent.from_tools(
            tools=query_engine_tools,
            llm=llm,
            verbose=True,
            system_prompt=f"""\
    You are a specialized agent designed to answer queries about the `{paper_name}`.
    Be intelligent to choose the appropriate tool for answering the query. 
    Use vector_tool_{paper_name} for answering generic query.
    Use summary_tool_{paper_name} for answering questions related to summarization.
    You must ALWAYS use at least one of the tools provided when answering a question;
    Do NOT rely on prior knowledge else you will be heavily penalized.
    """,
        )

        return agent, summary

    def build_agents(self, folder_path, paper_lookup):
        """
        Build agents for multiple documents.

        Parameters:
        folder_path (str): Path to the folder containing the documents.
        paper_lookup (dict): Dictionary mapping filenames to metadata.

        Returns:
        tuple: (agents_dict, extra_info_dict) where agents_dict contains agents for each paper
               and extra_info_dict contains summaries and nodes for each paper.
        """
        def get_paper_metadata(filename):
            # Helper function to get metadata for a paper given its filename
            return paper_lookup[os.path.basename(filename)]

        # Dictionaries to hold the agents and additional information
        agents_dict = {}
        extra_info_dict = {}
        
        # Iterate through all papers and build agents
        for idx, paper_name in enumerate(tqdm(paper_lookup, desc='Building Agents', total=len(paper_lookup))):
            # Create file path for each paper
            paper_file_path = os.path.join(folder_path, paper_name)
            
            # Load the document using a directory reader and get the nodes
            reader = SimpleDirectoryReader(
                input_files=[paper_file_path],
                file_metadata=get_paper_metadata,
            ).load_data()
            nodes = self.node_parser.get_nodes_from_documents(reader)

            # Build an agent for the document
            agent, summary = self.build_agent_per_doc(nodes, paper_name[:-4])

            # Store the agent and additional info in the dictionaries
            agents_dict[paper_name] = agent
            extra_info_dict[paper_name] = {"summary": summary, "nodes": nodes}

        return agents_dict, extra_info_dict

class ArxivBuilder():
    """
    A class to handle fetching papers from Arxiv, downloading them, and building agents for each paper.
    """

    def __init__(
        self,
        search_query: str,
        persist: Optional[bool] = False,
        papers_dir: Optional[str] = ".papers",
        max_results: Optional[int] = 10,
    ) -> None:
        """
        Initialize with parameters.
        
        Args:
            search_query (str): A topic to search for (e.g. "Artificial Intelligence").
            persist (Optional[bool]): Whether to store the paper on local disk.
            papers_dir (Optional[str]): Local directory to store the papers.
            max_results (Optional[int]): Maximum number of papers to fetch.
        """
        self.agent_builder = PaperAgentBuilder()
        self.agents_dict = {}
        self.extra_info_dict = {}
        self.paper_lookup = {}
        self.search_query = search_query
        self.persist = persist
        self.papers_dir = papers_dir
        self.max_results = max_results
        self.tools = []

    def download_paper_and_build_agent(self):
        """
        - Search for a topic on Arxiv.
        - Download the PDFs of the top results locally then read them.
        - Build an agent for each paper.
        """
        import arxiv
        
        # Search for papers on Arxiv using the specified query and parameters.
        arxiv_search = arxiv.Search(
            query=self.search_query,
            id_list=[],
            max_results=self.max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )
        search_results = list(arxiv_search.results())
        print(f"> Successfully fetched {len(search_results)} papers")
            

        # Ensure the directory to store papers exists.
        if not os.path.exists(self.papers_dir):
            os.makedirs(self.papers_dir)

        # Prepare a dictionary to hold paper metadata and download the papers.
        self.paper_lookup = {}
        for paper in search_results:
            # Create a filename from the paper's entry ID
            filename = paper.entry_id.split('/')[-1].replace('.', '_') + '.pdf'
            # Store paper metadata in the lookup dictionary.
            self.paper_lookup[filename] = {
                "Title of this paper": paper.title,
                "Authors": ", ".join([a.name for a in paper.authors]),
                "Date published": paper.published.strftime("%m/%d/%Y"),
                "URL": paper.entry_id,
                "summary": paper.summary
            }
            # Download the paper PDF.
            paper.download_pdf(dirpath=self.papers_dir, filename=filename)
            print(f"> Downloading {filename}...")

        # Build agents for the downloaded papers.
        self.agents_dict, self.extra_info_dict = self.agent_builder.build_agents(self.papers_dir, self.paper_lookup)

        # If persistence is not required, delete the downloaded papers and directory.
        if not self.persist:
            try:
                for f in list(self.paper_lookup.keys()):
                    os.remove(os.path.join(self.papers_dir, f))
                    print(f"> Deleted file: {f}")
                os.rmdir(self.papers_dir)
                print(f"> Deleted directory: {self.papers_dir}")
            except OSError:
                print("Unable to delete files or directory")

    def get_tools(self):
        """
        Get the tools (agents) created for each paper.
        
        Returns:
            list: List of QueryEngineTool instances for each paper.
        """
        # Reset the tools list
        self.tools = []
        # Iterate through each agent and build tool
        for file_name, agent in self.agents_dict.items():
            summary = self.extra_info_dict[file_name]["summary"]
            # Create a QueryEngineTool for each agent, with the corresponding summary as metadata.
            doc_tool = QueryEngineTool(
                query_engine=agent,
                metadata=ToolMetadata(
                    name=f"tool_{file_name[:-4]}",  # Use the file name without extension.
                    description=summary,  # Use the paper's summary as the description.
                ),
            )
            # Add the tool to the list of tools.
            self.tools.append(doc_tool)

        return self.tools

    def run(self):
        """
        Execute the process of downloading papers, building agents, and returning the tools.

        Returns:
            list: A list of QueryEngineTool instances for querying the papers.
        """
        try:
            # Attempt to download papers and build agents
            self.download_paper_and_build_agent()

            # Retrieve and return tools for querying
            return self.get_tools()

        except Exception as e:
            # Handle any exceptions that occur during the process
            print(f"> Not able to download any paper: {e}")
            return None
