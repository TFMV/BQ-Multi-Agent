# BQ Multi-Agent API

![BQ Analyst](assets/bqagent.webp)

## Overview

The BQ Multi-Agent API is a Flask-based application that leverages multiple agents to interact with Google BigQuery for data analysis. The API is designed to accept SQL queries, execute them against BigQuery, and provide the results in a structured JSON format. Additionally, the application includes a health check endpoint to ensure the service is running correctly.

## Technology Stack

- **Flask:** A lightweight WSGI web application framework in Python, used to create the API endpoints.
- **Google Cloud BigQuery:** A fully-managed, serverless data warehouse that allows for fast SQL queries using the processing power of Google's infrastructure.
- **CrewAI:** A framework for building and managing AI agents that perform specific tasks, such as querying databases, analyzing data, and ensuring quality.
- **Pandas:** A data manipulation and analysis library for Python, used here to handle query results.
- **Gunicorn:** A Python WSGI HTTP Server for UNIX, used to serve the Flask application.

## Flow

1. **Initialization:**
    - Environment variables are loaded from a `.env` file, including the OpenAI API key and Google Cloud credentials.
    - A BigQuery client is initialized to interact with BigQuery.
    - Three agents are defined using CrewAI, each with a specific role: querying data, analyzing data, and ensuring quality of the analysis.

2. **Agent Definitions:**
    - **Query Agent:** Executes SQL queries against BigQuery and retrieves the data.
    - **Analysis Agent:** Analyzes the queried data, generating insights and visualizations.
    - **Quality Assurance (QA) Agent:** Reviews the analysis for accuracy, completeness, and actionable insights.

3. **Task Definitions:**
    - **Query Task:** Uses the Query Agent to execute SQL queries and retrieve data.
    - **Analysis Task:** Uses the Analysis Agent to analyze the data and produce a detailed report.
    - **QA Task:** Uses the QA Agent to review the analysis report and provide feedback.

4. **Crew Definition:**
    - The agents and tasks are combined into a CrewAI crew, orchestrating the overall data analysis workflow.

5. **API Endpoints:**
    - **/analyze:** Accepts a JSON payload containing an SQL query, runs the data analysis workflow, and returns the results.
    - **/health:** Provides a simple health check to verify the service status.

## Example Workflow

1. **Client Request:**
    - A client sends a POST request to the `/analyze` endpoint with a JSON payload containing an SQL query.

2. **Query Execution:**
    - The Query Agent executes the provided SQL query against BigQuery.
    - The results are retrieved and passed to the Analysis Agent.

3. **Data Analysis:**
    - The Analysis Agent analyzes the retrieved data, generating visualizations and statistical summaries.
    - The analysis results are then passed to the QA Agent.

4. **Quality Assurance:**
    - The QA Agent reviews the analysis report for accuracy, completeness, and clarity.
    - Any feedback or suggestions for improvement are noted, and the final report is prepared.

5. **Response:**
    - The API returns the final analysis report in JSON format to the client.

## License

This project is licensed under the MIT License.

