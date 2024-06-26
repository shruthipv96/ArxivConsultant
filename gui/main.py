# Import the tkinter module for creating graphical user interfaces
import tkinter as tk

# Import the scrolledtext module from tkinter for creating a scrollable text widget
from tkinter import scrolledtext

# Import the ArxivBuilder class from the arxiv_builder module
# This class is responsible for building Arxiv search queries and retrieving papers
from arxiv_builder import ArxivBuilder

# Import the build_arxiv_agent function from the arxiv_consultant module
# This function is used to create an agent that can interact with the retrieved Arxiv papers
from arxiv_consultant import build_arxiv_agent

# Import the threading module for running tasks in separate threads
# This allows the GUI to remain responsive while performing long-running operations
import threading

# ----------------------------------------------------------------------
# Main driver class
# ----------------------------------------------------------------------
class ConsultantUI:
    def __init__(self, root):
        '''Initialize the main window'''
        self.root = root
        self.root.title("Arxiv Consultant")
        self.welcome_message = "Welcome to Arxiv Consultant! Please set the search query and the count of relevant papers to retrieve"

        # Configure colors for tags
        self.tag_colors = {
            'user': {'foreground': 'black', 'background': 'orange'},
            'bot': {'foreground': 'black', 'background': 'lightgreen'}
        }

        # Frame for input fields
        input_frame = tk.Frame(root)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky='ew')
        input_frame.columnconfigure(3, weight=1)  # Make the fourth column expandable

        # Labels and text boxes for Max Papers and Search Query on the same row
        self.max_papers_label = tk.Label(input_frame, text="Max papers")
        self.max_papers_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')

        self.max_papers_text = tk.StringVar()
        self.max_papers_entry = tk.Entry(input_frame, textvariable=self.max_papers_text, width=10)
        self.max_papers_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')

        self.search_query_label = tk.Label(input_frame, text="Search Query")
        self.search_query_label.grid(row=0, column=2, padx=5, pady=5, sticky='e')

        self.search_query_text = tk.StringVar()
        self.search_query_entry = tk.Entry(input_frame, textvariable=self.search_query_text, width=50)
        self.search_query_entry.grid(row=0, column=3, padx=5, pady=5, sticky='ew')

        # Set button
        self.set_button = tk.Button(input_frame, text="Set", command=self.set_arxiv_context, width=10)
        self.set_button.grid(row=0, column=4, padx=10, pady=5)

        # Chat display
        self.chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, state='disabled', height=15)
        self.chat_display.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
        self.chat_display.tag_configure('user', foreground=self.tag_colors['user']['foreground'], background=self.tag_colors['user']['background'], justify='right')
        self.chat_display.tag_configure('bot', foreground=self.tag_colors['bot']['foreground'], background=self.tag_colors['bot']['background'], justify='left')

        # Frame for chat entry, send button, and reset button
        entry_frame = tk.Frame(root)
        entry_frame.grid(row=2, column=0, padx=10, pady=10, sticky='ew')
        entry_frame.columnconfigure(0, weight=1)  # Make the entry box expandable

        # Entry box for chat
        self.entry_text = tk.StringVar()
        self.entry_box = tk.Entry(entry_frame, textvariable=self.entry_text, width=80)
        self.entry_box.grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        self.entry_box.bind("<Return>", self.send_message)

        # Send button
        self.send_button = tk.Button(entry_frame, text="Send", command=self.send_message)
        self.send_button.grid(row=0, column=1, padx=5, pady=5)

        # Reset button
        self.reset_button = tk.Button(entry_frame, text="Reset", command=self.reset_ui)
        self.reset_button.grid(row=0, column=2, padx=5, pady=5, sticky='w')

        # Initial button states
        self.set_button.config(state='normal')
        self.send_button.config(state='disabled')
        self.reset_button.config(state='disabled')

        # Initialize UI state
        self.reset_ui()

        # Configure grid weights for resizing
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

    def reset_ui(self):
        """Reset the user interface to its initial state."""
        # Clear the chat display
        self.chat_display.config(state='normal')
        self.chat_display.delete('1.0', tk.END)
        self.chat_display.config(state='disabled')
        # Reset input fields
        self.entry_text.set("")
        self.max_papers_text.set("10")
        self.search_query_text.set("")
        # Display the welcome note again
        self.bot_msg(self.welcome_message)
        # Reset backend variables
        self.arxiv_agent = None
        self.arxiv_builder = None
        # Reset button states
        self.set_button.config(state='normal')
        self.send_button.config(state='disabled')
        self.reset_button.config(state='disabled')

    def disable_ui(self):
        """Disable all user inputs to prevent interaction during long operations."""
        self.max_papers_entry.config(state='disabled')
        self.search_query_entry.config(state='disabled')
        self.set_button.config(state='disabled')
        self.entry_box.config(state='disabled')
        self.send_button.config(state='disabled')
        self.reset_button.config(state='disabled')

    def enable_ui(self):
        """Enable all user inputs to allow interaction."""
        self.max_papers_entry.config(state='normal')
        self.search_query_entry.config(state='normal')
        self.set_button.config(state='normal')
        self.entry_box.config(state='normal')
        self.send_button.config(state='normal')
        self.reset_button.config(state='normal')

    def display_message(self, message, tag):
        """Display a message in the chat display with the specified tag (user or bot)."""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, f"{message}\n", tag)
        self.chat_display.tag_add(tag, 'end-1c linestart', 'end-1c lineend+1c')
        self.chat_display.tag_configure(tag, background=self.tag_colors[tag]['background'])
        self.chat_display.config(state='disabled')
        self.chat_display.yview(tk.END)  # Scroll to the end

    def bot_msg(self, data):
        """Display a bot message in the chat display."""
        self.display_message(data, 'bot')

    def user_msg(self, data):
        """Display a user message in the chat display."""
        self.display_message(data, 'user')

    def set_arxiv_context(self):
        """Set the context for the Arxiv search and build the Arxiv agent."""
        # Retrieve the values from UI input fields
        max_papers = int(self.max_papers_text.get())
        search_query = self.search_query_text.get()

        # Check if search query is not empty and max papers count is greater than zero
        if search_query.strip() != "" and max_papers != 0:
            # Display a message confirming the settings being applied
            self.bot_msg(f"\nBuilding Tools for the setting: Max papers = {max_papers}, Search Query = {search_query}")

            # Notify the user that the operation may take some time
            self.bot_msg("\nPlease wait, this might take a few minutes...\n")
            self.bot_msg("-"*50)

            # Disable the UI to prevent further interaction during the operation
            self.disable_ui()

            # Start a new thread to asynchronously build the Arxiv agents
            build_thread = threading.Thread(target=self.build_agents, args=(search_query, max_papers))
            build_thread.start()
        else:
            # If the input values are invalid, notify the user
            self.bot_msg("\nProvide valid search query and max papers count!\n")

    def build_agents(self, search_query, max_papers=10):
        """Build the Arxiv agents based on the search query and maximum number of papers."""
        # Initialize an instance of ArxivBuilder to search for papers matching the query term.
        self.arxiv_builder = ArxivBuilder(search_query=search_query, persist=True, max_results=max_papers)

        # Execute the ArxivBuilder to download papers, build agents, and retrieve tools.
        tools = self.arxiv_builder.run()

        if tools is not None:
            # If tools were successfully retrieved, print a section divider.
            self.bot_msg("-"*50)
            self.bot_msg("Papers I have knowledge on")

            # Iterate over the papers retrieved by ArxivBuilder and print their titles.
            for paper in self.arxiv_builder.paper_lookup.values():
                self.bot_msg(f"> {paper['Title of this paper']}")

            # Print another section divider for clarity.
            self.bot_msg("-"*50)

            # Build the arxiv_agent using tools obtained from arxiv_builder.
            self.arxiv_agent = build_arxiv_agent(self.arxiv_builder)

            # Reset the state of arxiv_agent to ensure it starts fresh for the conversation.
            self.arxiv_agent.reset()
        else:
            # If no tools were retrieved (possibly due to search failure), notify the user.
            self.bot_msg("> Retry using a different search term.")
            self.bot_msg("-"*50)

        # Enable the UI after completing the operation
        self.enable_ui()

        # Set the states of buttons to reflect the current UI state
        self.set_button.config(state='disabled')
        self.send_button.config(state='normal')
        self.reset_button.config(state='normal')


    def send_message(self, event=None):
        """Send the user message and get a response from the Arxiv agent."""
        # Retrieve the user's message from the entry text box
        user_message = self.entry_text.get()
        
        # Check if the message is not empty
        if user_message.strip() != "":
            # Clear the entry box after retrieving the message
            self.entry_text.set("")
            
            # Display the user's message in the chat display
            self.user_msg(user_message)
            
            # Disable the UI to prevent further interaction while processing the message
            self.disable_ui()
            
            # Create a new thread to handle getting a response from the Arxiv agent
            # This keeps the UI responsive by running the potentially long operation in the background
            chat_thread = threading.Thread(target=self.get_chat_response, args=(user_message,))
            chat_thread.start()

    def get_chat_response(self, message):
        """Get a response from the Arxiv agent based on the user message."""
        # Use the Arxiv agent to get a response to the user's message
        response = self.arxiv_agent.chat(message)
        
        # Re-enable the UI to allow user interaction after the response is received
        self.enable_ui()
        
        # Display the agent's response in the chat display
        self.bot_msg(response)

if __name__ == "__main__":
    # Create the main window for the Tkinter application
    root = tk.Tk()
    
    # Instantiate the ConsultantUI class, passing the main window as an argument
    # This sets up the user interface for the Arxiv Consultant
    chatbot_ui = ConsultantUI(root)
    
    # Start the Tkinter event loop, which waits for user interaction and updates the UI
    root.mainloop()

