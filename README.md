# Comacks Dental Agent

A conversational AI assistant for Comacks Dental built with Streamlit, LangGraph, and Google's Gemini AI.

## Features

- **Intelligent Chatbot**: Powered by Gemini 2.5 Flash for natural conversations
- **Doctor Recommendations**: Suggests appropriate doctors based on user needs
- **Appointment Booking**: Integrated booking form with validation
- **Service Information**: Provides details on dental services
- **Emergency Support**: Quick access to emergency contact information
- **Memory**: Maintains conversation history for contextual responses

## Prerequisites

- Python 3.11.0
- Google API Key for Gemini AI

## Installation

1. Clone or download this repository
2. Navigate to the project directory
3. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Get a Google API key from [Google AI Studio](https://aistudio.google.com/apikey)
2. Replace the placeholder API key in `agent.py`:
   ```python
   os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY_HERE"
   ```

## Running the Application

1. Ensure you're in the project directory
2. Run the Streamlit app:
   ```bash
   python -m streamlit run app.py
   ```
3. Open your browser to `http://localhost:8501`

## Project Structure

- `agent.py`: LangGraph-based conversational agent logic
- `app.py`: Streamlit web interface
- `requirements.txt`: Python dependencies
- `README.md`: This file

## Usage

1. Start a conversation by typing messages
2. Use buttons for quick actions like booking appointments or viewing doctors
3. The AI remembers the conversation context
4. Fill out the booking form when ready to schedule

## Technologies Used

- **Streamlit**: Web framework for the UI
- **LangGraph**: Workflow orchestration for the agent
- **LangChain Google GenAI**: Integration with Gemini models
- **Python 3.11**: Programming language

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is for educational purposes. Please check Google's terms of service for API usage.
