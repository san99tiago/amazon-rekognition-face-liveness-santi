import React from "react";
import { useEffect } from "react";
import { Loader } from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";
import { FaceLivenessDetector } from "@aws-amplify/ui-react-liveness";
import customVars from "./vars";
import { DynamoDBClient, PutItemCommand } from "@aws-sdk/client-dynamodb";
import { fetchAuthSession } from "@aws-amplify/auth";

function FaceLiveness({ faceLivenessAnalysis }) {
  const [loading, setLoading] = React.useState(true);
  const [sessionId, setSessionId] = React.useState(null);

  const endpoint = process.env.REACT_APP_ENV_API_URL
    ? process.env.REACT_APP_ENV_API_URL
    : customVars.REACT_APP_ENV_API_URL;

  useEffect(() => {
    /*
     * API call to create the Face Liveness Session
     */
    const fetchCreateLiveness = async () => {
      const response = await fetch(endpoint + "createfacelivenesssession");
      const data = await response.json();
      setSessionId(data.sessionId);
      setLoading(false);
    };

    fetchCreateLiveness();
  }, [endpoint]);

  /*
   * Function to add an item to DynamoDB (user sessions)
   */
  const addItemToDynamoDB = async () => {
    // Load IAM session
    const session = await fetchAuthSession();

    // TOKEN management
    const token = session?.tokens?.idToken;
    console.debug("Token: ", token.toString());
    const decodedToken = JSON.parse(atob(token.toString().split(".")[1]));
    console.debug("Decoded Token: ", decodedToken);
    const phoneNumber = decodedToken["phone_number"];
    console.info("Phone Number: ", phoneNumber);
    const sanitizedPhoneNumber = phoneNumber.replace(/\+/g, "");
    console.info("Sanitized Phone Number: ", sanitizedPhoneNumber);

    const ttl = Math.floor(Date.now() / 1000) + 120; // 2 minutes from now
    const params = {
      TableName: "rufus-bank-auth-sessions-prod",
      Item: {
        PK: { S: `USER#${sanitizedPhoneNumber}` },
        SK: { S: "AUTH" },
        active: { BOOL: true },
        ttl: { N: ttl.toString() },
      },
    };

    // DYNAMODB CLIENT management
    let dynamodbClient = new DynamoDBClient({
      region: "us-east-1",
      credentials: session?.credentials, // Ensure this returns the correct credentials
    });

    try {
      await dynamodbClient.send(new PutItemCommand(params));
      console.log("Item added to DynamoDB successfully.");
    } catch (error) {
      console.error("Error adding item to DynamoDB:", error);
    }
  };

  /*
   * Get the Face Liveness Session Result
   */
  const handleAnalysisComplete = async () => {
    const response = await fetch(endpoint + "getfacelivenesssessionresults", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ sessionid: sessionId }),
    });
    const data = await response.json();
    console.log("DEBUG_SANTI...");
    console.log(data);

    // const faceLivenessScore = data.body?.faceLivenessScore;
    const faceLivenessScore = data.body?.Confidence;

    if (faceLivenessScore && faceLivenessScore > 70) {
      console.log(
        "Success: User biometric auth OK. Proceeding to Store session in DynamoDB..."
      );
      await addItemToDynamoDB();

      // Show alert to tell user to return to WhatsApp
      const alertContainer = document.createElement("div");
      alertContainer.style.position = "fixed";
      alertContainer.style.top = "50%";
      alertContainer.style.left = "50%";
      alertContainer.style.transform = "translate(-50%, -50%)";
      alertContainer.style.padding = "30px";
      alertContainer.style.backgroundColor = "#4CAF50";
      alertContainer.style.color = "white";
      alertContainer.style.borderRadius = "12px";
      alertContainer.style.boxShadow = "0 8px 10px rgba(0, 0, 0, 0.2)";
      alertContainer.style.fontSize = "20px";
      alertContainer.style.fontWeight = "bold";
      alertContainer.style.textAlign = "center";
      alertContainer.textContent = "✅ Return to WhatsApp";

      document.body.appendChild(alertContainer);

      setTimeout(() => {
        document.body.removeChild(alertContainer);
      }, 3000);
    } else {
      console.warn("Face liveness score is too low. Not adding to DynamoDB.");
    }

    faceLivenessAnalysis(data.body);
  };

  return (
    <>
      <h1 style={{ textAlign: "center", marginBottom: "20px" }}>
        RUFUS BANK AUTH
      </h1>
      {loading ? (
        <Loader />
      ) : (
        <FaceLivenessDetector
          sessionId={sessionId}
          region="us-east-1"
          onAnalysisComplete={handleAnalysisComplete}
          onError={(error) => {
            console.error(error);
          }}
        />
      )}
    </>
  );
}

export default FaceLiveness;
