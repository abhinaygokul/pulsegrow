# How to Create a YouTube Data API Key

To enable real data fetching for PulseGrow, you need a YouTube Data API Key. Follow these steps:

1.  **Go to Google Cloud Console**:
    Visit [https://console.cloud.google.com/](https://console.cloud.google.com/) and log in.

2.  **Create a Project**:
    -   Click the project dropdown in the top bar.
    -   Select **"New Project"**.
    -   Name it (e.g., "PulseGrow") and click "Create".

3.  **Enable the API**:
    -   In the left sidebar, go to **"APIs & Services" > "Library"**.
    -   Search for **"YouTube Data API v3"**.
    -   Click on the result and then click the **"Enable"** button.

4.  **Create Credentials**:
    -   After enabling, click **"Create Credentials"** (top right) or go to **"APIs & Services" > "Credentials"**.
    -   Click **"+ CREATE CREDENTIALS"** and select **"API Key"**.

5.  **Copy the Key**:
    -   Your new API key will be displayed.
    -   Copy it and paste it into our chat.

> **Tip**: Since you already have a Gemini API key, you can use the *same* project. Just enable the "YouTube Data API v3" in that project, and your existing key *might* work (or simply create a new one in the same project).
