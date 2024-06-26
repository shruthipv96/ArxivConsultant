# ----------------------------------------------------------------------
# Import Libraries
# ----------------------------------------------------------------------

# Core components
from llama_index.core.objects import ObjectIndex, ObjectRetriever
from llama_index.core.schema import QueryBundle
from llama_index.core.query_engine import SubQuestionQueryEngine
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core import VectorStoreIndex
# Open AI components
from llama_index.llms.openai import OpenAI
# Post processor
from llama_index.core.postprocessor import SentenceTransformerRerank
# Global params
from global_params import llm, OPEN_AI_API_KEY, top_n_results

# ----------------------------------------------------------------------
# Retriever class
# ----------------------------------------------------------------------
class RelavantObjectRetriever(ObjectRetriever):
    """
    A class to retrieve relevant objects based on a query, process the nodes, and map them to tools.
    """
    def __init__(
        self,
        retriever,
        object_node_mapping,
        node_postprocessors=None,
        llm=None,
        builder=None
    ):
        """
        Initialize the RelavantObjectRetriever with necessary components.

        Args:
            retriever: An instance used to retrieve nodes based on a query.
            object_node_mapping: A mapping from nodes to objects/tools.
            node_postprocessors (Optional[list]): List of postprocessors to process nodes after retrieval.
            llm (Optional): Language model to use for querying.
        """
        self._retriever = retriever
        self._object_node_mapping = object_node_mapping
        self._llm = llm or OpenAI(model="gpt-3.5-turbo", api_key=OPEN_AI_API_KEY)  # Default to GPT-3.5 model if none provided.
        self._node_postprocessors = node_postprocessors or []  # Use provided postprocessors or an empty list.
        self._builder = builder

    def retrieve(self, query_bundle):
        """
        Retrieve relevant objects based on a query, process nodes, and return tools for querying.

        Args:
            query_bundle: Query or QueryBundle object containing the query string.

        Returns:
            list: A list of QueryEngineTool objects including a sub-question tool for comparisons.
        """
        # Convert string query to QueryBundle if necessary.
        if isinstance(query_bundle, str):
            query_bundle = QueryBundle(query_str=query_bundle)

        # Retrieve nodes using the provided retriever.
        nodes = self._retriever.retrieve(query_bundle)

        # Postprocess the retrieved nodes using the provided postprocessors.
        for processor in self._node_postprocessors:
            nodes = processor.postprocess_nodes(nodes, query_bundle=query_bundle)

        # Map nodes to tools using the object node mapping.
        tools = [self._object_node_mapping.from_node(n.node) for n in nodes]

        # Create a sub-question engine for comparison queries.
        sub_question_engine = SubQuestionQueryEngine.from_defaults(
            query_engine_tools=tools, llm=self._llm
        )
        sub_question_description = """\
Useful for any queries that involve comparing multiple documents. ALWAYS use this tool for comparison queries - make sure to call this \
tool with the original query. Do NOT use the other tools for any queries involving multiple documents.
"""
        # Define a tool for sub-question queries with metadata.
        sub_question_tool = QueryEngineTool(
            query_engine=sub_question_engine,
            metadata=ToolMetadata(
                name="compare_tool", description=sub_question_description
            ),
        )

        # Get paper names from the tools and retrieve all relevant nodes from the ArxivBuilder instance.
        paper_names = [tool.metadata.name.replace('tool_', '') + '.pdf' for tool in tools]
        all_nodes = []
        for name in paper_names:
            all_nodes.extend(self._builder.extra_info_dict[name]['nodes'])

        # Build a base index from all nodes and create a query engine for it.
        base_index = VectorStoreIndex(all_nodes)
        base_query_engine = base_index.as_query_engine(llm=self._llm, similarity_top_k=4)
        base_query_engine_tool = QueryEngineTool(
            query_engine=base_query_engine,
            metadata=ToolMetadata(
                name="base_query_engine",
                description="Contains the information of all the related documents in one tool",
            ),
        )

        # Return the list of tools including the sub-question tool and the base query engine tool.
        return tools + [sub_question_tool, base_query_engine_tool]

# ----------------------------------------------------------------------
# Method to create retriever object
# ----------------------------------------------------------------------
def create_object_retriever(builder):
    """
    Create an ObjectRetriever instance using tools from ArxivBuilder.

    Args:
        arxiv_builder (ArxivBuilder): An instance of ArxivBuilder containing tools and data.

    Returns:
        RelavantObjectRetriever: An ObjectRetriever instance configured with tools and postprocessors.
    """
    # We choose a model with relatively high speed and decent accuracy.
    # This model will rerank the top retrieved results using a cross-encoder model.
    rerank_postprocessor = SentenceTransformerRerank(
        model="cross-encoder/ms-marco-MiniLM-L-2-v2", top_n=top_n_results
    )

    # Create an ObjectIndex from the tools obtained from the ArxivBuilder instance.
    # The index_cls parameter specifies that we are using a VectorStoreIndex.
    obj_index = ObjectIndex.from_objects(
        builder.get_tools(),
        index_cls=VectorStoreIndex,
    )

    # Convert the ObjectIndex into a node retriever that retrieves nodes based on similarity.
    # The similarity_top_k parameter specifies the number of top similar nodes to retrieve.
    vector_node_retriever = obj_index.as_node_retriever(
        similarity_top_k=top_n_results,
    )

    # Wrap the node retriever with an ObjectRetriever to return objects instead of nodes.
    # The ObjectRetriever takes the following parameters:
    # - retriever: The node retriever created above.
    # - object_node_mapping: The mapping from nodes to objects, obtained from the ObjectIndex.
    # - node_postprocessors: A list of postprocessors to apply to the retrieved nodes, in this case, the rerank_postprocessor.
    # - llm: The language model to use for querying, assumed to be defined elsewhere in the code.
    obj_retriever = RelavantObjectRetriever(
        retriever=vector_node_retriever,
        object_node_mapping=obj_index.object_node_mapping,
        node_postprocessors=[rerank_postprocessor],
        llm=llm,  # llm is assumed to be defined elsewhere
        builder=builder
    )
    
    return obj_retriever
