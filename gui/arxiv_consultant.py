# ----------------------------------------------------------------------
# Import Libraries
# ----------------------------------------------------------------------

# Global params
from global_params import llm
# Core components
from llama_index.core.agent import ReActAgent
# Other components
from relevant_object_retreiver import create_object_retriever
from arxiv_builder import ArxivBuilder

# ----------------------------------------------------------------------
# Method to create top level agent 
# ----------------------------------------------------------------------
def build_arxiv_agent(arxiv_builder):
    """
    Build an instance of ReActAgent using tools provided by RelavantObjectRetriever.

    Args:
        arxiv_builder (ArxivBuilder): An instance of ArxivBuilder containing tools and data.

    Returns:
        ReActAgent: An instance of ReActAgent configured to respond to queries based on the provided tools.
    """
    # Create an instance of ReActAgent using the tools created using arxiv_builder.
    # The tool_retriever parameter initializes the tool retriever with tools for object retrieval.
    # The system_prompt parameter provides instructions on how the agent should respond to queries.
    agent = ReActAgent.from_tools(
        tool_retriever=create_object_retriever(arxiv_builder),
        system_prompt=""" \
    You are an IP consultant designed to answer queries about the documentation.
    ALWAYS use ONLY the AVAILABLE tools provided to answer a question. Do not rely on ANY PRIOR knowledge.
    You are responsible for the following tasks based on user query:
    1) Check if the user idea is relevant across any of the documents.
    2) If you are not able to provide answer with existing knowledge, respond with a note something like
      "The query looks like not in my knowledge. It might either be novel or my knowledge is limited"
    3) Strictly adhere to the provided knowledge, else you will be heavily PENALIZED.\
    """,
        llm=llm,  # The language model to use, assumed to be defined elsewhere in the code.
        verbose=True,  # Enable verbose mode for detailed logging.
        max_iterations=20, # Set the maximum iteration of the agent to 20 for more deeper search.
    )
    
    return agent

# ----------------------------------------------------------------------
# Main driver function which orchestrates the whole process
# ----------------------------------------------------------------------
def ArxivConsultant():
    # Prompt the user to provide a search query term for Arxiv.
    text_input = input("Provide the arxiv search term: ")

    # Provide a message indicating the user should wait, as fetching papers might take time.
    print("\nPlease wait, this might take a few minutes")
    print("-"*50)

    # Initialize an instance of ArxivBuilder to search for papers matching the query term.
    arxiv_builder = ArxivBuilder(search_query=text_input, persist=True, max_results=10)

    # Execute the ArxivBuilder to download papers, build agents, and retrieve tools.
    tools = arxiv_builder.run()

    if tools is not None:
        # If tools were successfully retrieved, print a section divider.
        print("-"*50)
        print("Papers I have knowledge on")

        # Iterate over the papers retrieved by ArxivBuilder and print their titles.
        for paper in arxiv_builder.paper_lookup.values():
            print(f"> {paper['Title of this paper']}")

        # Print another section divider for clarity.
        print("-"*50)
        print("> Type 'exit' to close the chat <")
        print("-"*50)

        # Build the arxiv_agent using tools obtained from arxiv_builder.
        arxiv_agent = build_arxiv_agent(arxiv_builder)

        # Reset the state of arxiv_agent to ensure it starts fresh for the conversation.
        arxiv_agent.reset()

        # Start an infinite loop to interact with the user until they choose to exit.
        while True:
            print("*"*50)
            # Prompt the user for input and wait for their response.
            text_input = input("User: ")

            # Check if the user wants to exit the interaction.
            if text_input == "exit":
                break  # Exit the loop if the user inputs "exit".

            # Send the user's input to arxiv_agent for processing and get the response.
            response = arxiv_agent.chat(text_input)

            # Print section divider for clarity.
            print("*"*50)

            # Print the response generated by arxiv_agent.
            print(f"Agent: {response}")
    else:
        # If no tools were retrieved (possibly due to search failure), notify the user.
        print("> Retry using a different search term.")
        print("> Exit...")
        print("-"*50)

if __name__ == '__main__':
    ArxivConsultant()