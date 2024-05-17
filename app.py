import os
import logging
import glob
from flask import Flask, request, jsonify
from google.cloud import bigquery
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from embedchain.vectordb.chroma import ChromaDbConfig
from embedchain.app import App

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Load your OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_MODEL_NAME"] = 'gpt-3.5-turbo'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = '/app/service-account-key.json'  # Path inside the Docker container

# Initialize BigQuery client
bq_client = bigquery.Client()

# Function to delete existing SQLite files
def delete_existing_sqlite_files():
    sqlite_files = glob.glob('/app/*.db')
    for file in sqlite_files:
        try:
            os.remove(file)
            logger.info(f"Deleted existing SQLite file: {file}")
        except Exception as e:
            logger.error(f"Error deleting SQLite file {file}: {e}")

# Call the function to delete existing SQLite files
delete_existing_sqlite_files()

# Define agents with memory and tools
def create_agent(role, goal, backstory):
    logger.debug(f"Creating agent with role: {role}")
    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        verbose=True
    )

query_agent = create_agent(
    role="BigQuery Specialist",
    goal="Query BigQuery datasets to retrieve relevant data",
    backstory="You are a specialist in querying BigQuery to extract meaningful data for analysis."
)

analysis_agent = create_agent(
    role="Data Analysis Specialist",
    goal="Analyze datasets and provide insightful visualizations and conclusions",
    backstory="You specialize in analyzing complex datasets and providing meaningful insights through visualizations and statistical methods."
)

qa_agent = create_agent(
    role="Quality Assurance Specialist",
    goal="Review the analysis results for accuracy, completeness, and clarity",
    backstory="You are an expert in ensuring the quality of data analysis, checking for accuracy, thoroughness, and actionable insights."
)

# Define tasks
query_task = Task(
    description=(
        "Execute the following SQL query on the BigQuery dataset:\n{sql_query}\n"
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

data_analysis_crew = Crew(
    agents=[query_agent, analysis_agent, qa_agent],
    tasks=[query_task, analysis_task, qa_task],
    verbose=True
)

# Create the Flask app
app = Flask(__name__)

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
    # Execute the SQL query using BigQuery client
    query_job = bq_client.query(sql_query)
    results = query_job.result().to_dataframe()
    logger.debug(f"Query results: {results}")

    inputs = {
        "sql_query": sql_query,
        "query_results": results.to_dict(orient='records')  # Convert DataFrame to list of dicts
    }
    logger.debug(f"Running data analysis with inputs: {inputs}")
    
    # Run analysis task
    analysis_result = data_analysis_crew.run_task(task=analysis_task, inputs=inputs)
    logger.debug(f"Analysis result: {analysis_result}")

    # Run QA task with analysis result
    qa_result = data_analysis_crew.run_task(task=qa_task, inputs=analysis_result)
    logger.debug(f"QA result: {qa_result}")

    # Combine analysis result and QA report
    combined_result = {
        "analysis_result": analysis_result,
        "qa_report": qa_result
    }

    return combined_result

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
