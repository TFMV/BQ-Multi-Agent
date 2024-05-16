import os
import logging
from flask import Flask, request, jsonify
from google.cloud import bigquery
from crewai import Agent, Task, Crew
from crewai_tools import BigQueryTool
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Load your OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'

# Initialize BigQuery client
bq_client = bigquery.Client()

# Define the BigQuery Tool
class BigQueryTool:
    def __init__(self, client):
        self.client = client

    def query(self, sql_query):
        try:
            query_job = self.client.query(sql_query)
            results = query_job.result()
            data = results.to_dataframe()
            logger.debug(f"Query executed successfully: {sql_query}")
            return data
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

# Define agents with memory and tools
query_agent = Agent(
    role="BigQuery Specialist",
    goal="Query BigQuery datasets to retrieve relevant data",
    backstory="You are a specialist in querying BigQuery to extract meaningful data for analysis.",
    tools=[BigQueryTool(bq_client)],
    memory=True,
    verbose=True
)

analysis_agent = Agent(
    role="Data Analysis Specialist",
    goal="Analyze datasets and provide insightful visualizations and conclusions",
    backstory="You specialize in analyzing complex datasets and providing meaningful insights through visualizations and statistical methods.",
    tools=[BigQueryTool(bq_client)],
    memory=True,
    verbose=True
)

qa_agent = Agent(
    role="Quality Assurance Specialist",
    goal="Review the analysis results for accuracy, completeness, and clarity",
    backstory="You are an expert in ensuring the quality of data analysis, checking for accuracy, thoroughness, and actionable insights.",
    tools=[BigQueryTool(bq_client)],
    memory=True,
    verbose=True
)

# Define tasks
query_task = Task(
    description=(
        "Query the BigQuery dataset with the following SQL query:\n{sql_query}\n"
        "Retrieve the results and pass them to the analysis agent."
    ),
    expected_output="A DataFrame containing the queried data.",
    agent=query_agent
)

analysis_task = Task(
    description=(
        "Analyze the provided dataset and generate visualizations and statistical summaries. "
        "Identify any significant patterns or correlations."
    ),
    expected_output=(
        "A detailed report with visualizations and statistical summaries, highlighting significant patterns and correlations in the data."
    ),
    agent=analysis_agent
)

qa_task = Task(
    description=(
        "Review the analysis report prepared by the Data Analysis Specialist. "
        "Ensure that the report is accurate, thorough, and provides actionable insights. "
        "Check for the following:\n"
        "- Accuracy: Verify the correctness of the data and calculations.\n"
        "- Completeness: Ensure all relevant aspects of the data are covered.\n"
        "- Clarity: Confirm that the report is clear and easy to understand.\n"
        "- Actionable Insights: Identify if the report provides clear and practical recommendations.\n"
        "Provide feedback and suggest any improvements if necessary."
    ),
    expected_output=(
        "A QA report confirming the accuracy and completeness of the analysis, "
        "along with any suggestions for improvement. Detailed feedback should include specific points on "
        "accuracy, completeness, clarity, and actionable insights."
    ),
    agent=qa_agent
)

# Define the crew
data_analysis_crew = Crew(
    agents=[query_agent, analysis_agent, qa_agent],
    tasks=[query_task, analysis_task, qa_task],
    verbose=True,
    memory=True
)

# Create the Flask app
app = Flask(__name__)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    logger.debug("Health check endpoint hit")
    return jsonify({"status": "healthy"}), 200

# Define the API endpoint
@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    sql_query = data.get('sql_query')
    logger.debug(f"Received SQL query: {sql_query}")
    if not sql_query:
        return jsonify({"error": "sql_query is required"}), 400
    
    try:
        result = run_data_analysis(sql_query)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in run_data_analysis: {e}")
        return jsonify({"error": str(e)}), 500

# Define the main function to execute the crew
def run_data_analysis(sql_query):
    inputs = {
        "sql_query": sql_query
    }
    logger.debug(f"Running data analysis with inputs: {inputs}")
    result = data_analysis_crew.kickoff(inputs=inputs)
    logger.debug(f"Data analysis result: {result}")
    return result

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))