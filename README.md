# Nursing Home Staff Scheduler

This project is a Streamlit application that generates optimal staff schedules for nursing homes using Mixed-Integer Linear Programming (MILP) with the PuLP library. It can use either mock data or CSV files for employee and shift information. The application is containerized using Docker for easy deployment and reproducibility.

## Features

*   **Flexible Input:** Uses either mock data (with customizable parameters) or user-provided CSV files for employee and shift data.
*   **Optimization:** Employs a MILP model to generate schedules that meet staffing requirements, respect employee availability, and minimize a simple objective function (total shifts worked).  The objective and constraints can be easily extended.
*   **User-Friendly Interface:**  Built with Streamlit for an interactive web-based interface.
*   **Downloadable Schedules:**  Allows users to download the generated schedule as a CSV file.
*   **Dockerized:**  Packaged as a Docker container for easy deployment and consistent execution across different environments.

## Prerequisites

*   Docker installed on your system.

## Getting Started

### 1. Build the Docker Image

Clone this repository (if you haven't already) and navigate to the project directory in your terminal:

```bash
git clone <repository_url>  # Replace with the actual URL if you have it on a git repo
cd <repository_directory>
docker build -t nursing-scheduler .
docker run -p 8501:8501 nursing-scheduler
