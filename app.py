from flask import Flask, request, render_template, session, jsonify
import numpy as np
import pandas as pd
import requests
import openai
import os
import json
import time
import joblib
from openai import OpenAI



# Initialize the Flask application
app = Flask(__name__)


# Set the secret key for the Flask application from an environment variable
app.secret_key = 'abc123secretkey'


# Instantiate the OpenAI client with API key from environment variable
client = OpenAI(api_key= 'RETRACTED FOR UPLOADING PURPOSES')


# Load the predictive model from a file
loaded_model = joblib.load('random_forest_model.pkl')
print("Model loaded successfully.")


# Define the column names for the model input
columns = ['no_of_dependents', 'education', 'self_employed', 'income_annum',
           'loan_amount', 'loan_term', 'cibil_score', 'residential_assets_value',
           'commercial_assets_value', 'luxury_assets_value', 'bank_asset_value']



def chatGPT(text):
    """
    Generates a response from the OpenAI's GPT model based on the given text.

    This function uses the OpenAI's GPT model to generate a response for a given text input.
    It specifies the model and sets parameters like max_tokens and temperature for the response.

    Args:
    text (str): The text input for which a response is required.

    Returns:
    str: The generated response text from the model.
    """
    completion = client.completions.create(
        model="text-davinci-003",
        prompt=text,
        max_tokens=4000,
        temperature=0.6
    )
    return print(completion.choices[0].text)




def get_response(prompt, model="gpt-3.5-turbo"):
    """
    Generates a chat response using OpenAI's GPT-3.5-turbo model based on the given prompt.

    This function creates a chat completion using the specified model. It sets the context of the chat 
    as a loan acceptance prediction and assistant for small business enterprises and then generates a 
    response to the user's prompt.

    Args:
    prompt (str): The prompt text from the user.
    model (str): The name of the GPT model to use. Defaults to "gpt-3.5-turbo".

    Returns:
    str: The chat response generated by the model.
    """
    messages = [
        {"role": "system", "content": "You are a nice loan acceptance prediction and assistant for small business enterprises"},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0
    )

    return response.choices[0].message.content






def get_predict_message(country):
    """
    Generates a custom message prompt for requesting information about loan sources for small business establishment.
    
    The function constructs a message prompt asking for a comprehensive list of organizations 
    in both the specified country and other countries that can provide loans for small businesses. 
    The prompt requests the information to be formatted in a specific JSON structure.

    Args:
    country (str): The name of the country for which the user wants loan information.

    Returns:
    tuple: A tuple containing the generated prompt and the response from get_response function.
    """

    # Define the required format for the response
    format = '''
    [
        {
            "myCountry": {
                "organizationName": "",
                "link": ""
            },
            "otherCountry": {
                "organizationName":"",
                "link": "",
                "Country": ""
            }
        },
        {
            "myCountry": {
                "organizationName": "",
                "link": ""
            },
            "otherCountry": {
                "organizationName":"",
                "link": "",
                "Country": ""
            }
        }
    ]
    '''
    
    # Construct the message prompt
    prompt = "Hi, my country is {}.Kindly act as a customer service bot for PNC Bank and tell me that you will reach out to me soon with more details about the loan soon.Give the answer strictly in this format: {}. Thanks.".format(country, format)

    # Generate the response for the prompt
    prompt_response = get_response(prompt)

    return prompt, prompt_response





def get_further_response(prediction, question, prev_prompt, prev_response):
    """
    Generates a new prompt based on a previous conversation and a prediction result, then gets a response to it.

    This function constructs a new prompt by appending additional context based on the prediction result to 
    the previous conversation. The conversation is capped at 2500 characters for conciseness. The new prompt 
    is then used to get a further response.

    Args:
    prediction (int): The prediction result (0 for 'Yes', 1 for 'No', others for neutral).
    question (str): The new question to be asked.
    prev_prompt (str): The previous prompt in the conversation.
    prev_response (str): The previous response in the conversation.

    Returns:
    tuple: A tuple containing the new prompt and the response from get_response function.
    """

    # Combine previous prompt and response
    old = str(prev_prompt) + str(prev_response)
    previous_conv = ""
    rev_old = old[::-1]

    # Extract the last 2500 characters of the reversed conversation
    for char in rev_old:
        if len(previous_conv) < 2500:
            previous_conv += char  # Fixed missing assignment operation

    # Reverse the extracted conversation back to original order
    final_previous_conv = previous_conv[::-1]

    # Append additional text based on prediction
    if prediction == 0:  # Yes
        add_text = "again congrats on your approved loan"
    elif prediction == 1:  # No
        add_text = 'again sorry about the unapproved loan'
    else:
        add_text = ""

    final_previous_conv += add_text

    # Construct the new prompt
    new_prompt = "Question: " + question + " | Previous Context: " + final_previous_conv + " | Instruction: Provide a concise, direct answer within 800 characters."

    # Generate the response for the new prompt
    further_response = get_response(new_prompt)

    return new_prompt, further_response








def get_business_idea(country, country_interest, capital_loan, amount, domain_interest, loan_pay_month):
    """
    Generates a prompt for business ideas based on user's financial situation and interests, and gets a response.

    This function creates a customized prompt asking for business ideas relevant to the user's specified domain 
    of interest and financial situation (either having capital or having taken a loan). It requests the response 
    to be formatted in a predefined JSON structure.

    Args:
    country (str): The user's home country.
    country_interest (str): The country where the user is interested in starting a business.
    capital_loan (str): A string indicating whether the user has 'capital' or has taken a 'loan'.
    amount (str): The amount of capital or loan in US Dollars.
    domain_interest (str): The domain of business interest.
    loan_pay_month (str): The time period (in months) for loan repayment, applicable if capital_loan is 'loan'.

    Returns:
    tuple: A tuple containing the generated prompt and the response from get_response function.
    """

    # Define the required format for the response
    format = '''
    [
        {
            "Business_Idea": "",
            "sector": "",
            "link": ""
        },
        {
            "Business Idea": "",
            "sector": "",
            "link": ""
        }
    ]
    '''
    
    # Construct the message prompt based on whether the user has capital or a loan
    if capital_loan == 'capital':
        prompt = "Hi, I'm from {}. Kindly help curate few nice business ideas, the domain sector of the business and like to learn more on the business, considering that I have a capital of {} US Dollars. My domain of business interest is {} and the country where I want to have my business is {}. Give the answer strictly in this format: {} Thanks.".format(country, amount, domain_interest, country_interest, format)
    elif capital_loan == 'loan':
        prompt = "Hi, I'm from {}. Kindly help curate few nice business ideas, the domain sector of the business and like to learn more on the business, considering that I got a loan of {} US Dollars and I am meant to pay back in {} months time. My domain of business interest is {} and the country where I want to have my business is {}. Give the answer strictly in this format: {} Thanks.".format(country, amount, loan_pay_month, domain_interest, country_interest, format)

    # Generate the response for the prompt
    idea_response = get_response(prompt)

    return prompt, idea_response







def get_financial_advice(country, country_interest, description, capital_loan, amount, domain_interest, loan_pay_month):
    """
    Generates a prompt for obtaining financial advice based on the user's financial status and business interests, and gets a response.

    This function creates a customized prompt asking for a comprehensive financial breakdown for managing a 
    business based on the user's financial situation (either having capital or a loan) and business interests. 
    It requests the response to be formatted in a predefined JSON structure.

    Args:
    country (str): The user's home country.
    country_interest (str): The country where the user is interested in starting a business.
    description (str): Description of the business or related query.
    capital_loan (str): A string indicating whether the user has 'capital' or has taken a 'loan'.
    amount (str): The amount of capital or loan in US Dollars.
    domain_interest (str): The domain of business interest.
    loan_pay_month (str): The time period (in months) for loan repayment, applicable if capital_loan is 'loan'.

    Returns:
    tuple: A tuple containing the generated prompt and the response from get_response function.
    """

    # Define the required format for the response
    format = '''
    {
        "financial_breakdown": "",
        "link": ""
    }
    '''
    
    # Construct the message prompt based on whether the user has capital or a loan
    if capital_loan == 'capital':
        prompt = "Hi, I'm from {}. Kindly help curate a comprehensive financial breakdown with link to read more on it, for how I would manage my business considering that I have a capital of {} US Dollars. My domain of business interest is {}, the description is: {} and the country where I want to have my business is {}. Make your answer strictly in this format: {}.".format(country, amount, domain_interest, description, country_interest, format)
    elif capital_loan == 'loan':
        prompt = "Hi, I'm from {}. Kindly help curate a comprehensive financial breakdown with link to read more on it, for how I would manage my business considering that I got a loan of {} US Dollars and I am meant to pay back in {} months time. My domain of business interest is {}, the description is: {} and the country where I want to have my business is {}. Make your answer strictly in this format: {}.".format(country, amount, loan_pay_month, domain_interest, description, country_interest, format)

    # Generate the response for the prompt
    advice_response = get_response(prompt)

    return prompt, advice_response








model= None


@app.route('/', methods=["GET", "POST"])
def main():
    """
    Route for the main page of the application.

    This route handles both GET and POST requests and renders the 'index.html' template,
    which is typically the homepage or landing page of the application.

    Returns:
    render_template: Renders the 'index.html' template.
    """
    return render_template('index.html')



@app.route('/form_predict', methods=["GET", "POST"])
def form_predict():
    """
    Route for the prediction form page.

    This route renders the 'form_predict.html' template, which usually contains a form
    for users to input data for predictions.

    Returns:
    render_template: Renders the 'form_predict.html' template.
    """
    return render_template('form_predict.html')



@app.route('/form_business_idea', methods=["GET", "POST"])
def form_business_idea():
    """
    Route for the business idea form page.

    This route renders the 'form_business_idea.html' template, where users can input information
    to get suggestions or advice on business ideas.

    Returns:
    render_template: Renders the 'form_business_idea.html' template.
    """
    return render_template('form_business_idea.html')



@app.route('/sign_in', methods=["GET", "POST"])
def sign_in():
    """
    Route for the sign-in page.

    This route renders the 'sign_in.html' template, which typically contains a form for
    user authentication (login).

    Returns:
    render_template: Renders the 'sign_in.html' template.
    """
    return render_template('sign_in.html')
       

@app.route('/services', methods=["GET", "POST"])
def services():
    """
    Route for the services page.

    This route renders the 'services.html' template, which typically lists the services
    or features offered by the application.

    Returns:
    render_template: Renders the 'services.html' template.
    """
    return render_template('services.html')



@app.route('/form_financial_advice', methods=["GET", "POST"])
def form_financial_advice():
    """
    Route for the financial advice form page.

    This route renders the 'form_financial_advice.html' template, where users can input details
    to receive financial advice or information.

    Returns:
    render_template: Renders the 'form_financial_advice.html' template.
    """
    return render_template('form_financial_advice.html')




@app.route('/next_session', methods=["GET", "POST"])
def next_session():
    """
    Route to process form data and redirect to the services page.

    This route handles the form submission from a previous page, extracts the user's name and country,
    and stores them in the session. It then renders the 'services.html' template, passing the user's 
    name and country for personalized content.

    The name is capitalized for consistency in display.

    Returns:
    render_template: Renders the 'services.html' template with user's name and country.
    """

    # Extract and process form data
    name = request.form['name'].capitalize()  # Capitalize the user's name
    country = request.form['country']         # Retrieve the user's country

    # Store data in session for future use
    session["name"] = name
    session["country"] = country

    # Render the services page with the user's name and country
    return render_template('services.html', country=country, name=name)




@app.route('/chat_predict', methods=["GET", "POST"])
def chat_predict():
    """
    Route to handle predictions based on user input from a chat interface.

    This route processes the form data submitted by the user, converts it into a format suitable 
    for prediction, and then uses a preloaded model to make a prediction. It also retrieves the user's 
    country and name from the session, and generates a prompt and response for further processing or display.

    Returns:
    render_template: Renders the 'chat_predict.html' template with prediction results and additional information.
    """

    # Extract form data
    depend = request.form['depend']
    education = request.form['education']
    employment = request.form['employment']
    income = request.form['income']
    loan_amount = request.form['loan_amount']
    loan_term = request.form['loan_term']
    score = request.form['score']
    resident = request.form['resident']
    commercial = request.form['commercial']
    luxury = request.form['luxury']
    bank = request.form['bank']

    # Prepare data for prediction
    columns = ['depend', 'education', 'employment', 'income', 'loan_amount', 'loan_term', 'score', 'resident', 'commercial', 'luxury', 'bank']
    arr = pd.DataFrame((np.array([[depend, education, employment, income, loan_amount, loan_term, score, resident, commercial, luxury, bank]])), columns=columns)
    pred = int(loaded_model.predict(arr)[0])

    # Retrieve user's country and name from session
    country = session.get("country", None)
    name = session.get("name", None)

    # Generate a prompt message and get response
    bot_predict_prompt, bot_predict_response = get_predict_message(country)

    # Convert the response to JSON format if needed
    bot_predict_response = json.loads(bot_predict_response)

    # Store prediction and responses in session
    session["pred"] = pred
    session["bot_predict_response"] = bot_predict_response
    session["bot_predict_prompt"] = bot_predict_prompt

    # Render the prediction page with necessary information
    return render_template('chat_predict.html', pred=pred, name=name, country=country, bot_predict_response=bot_predict_response)





@app.route('/further_predict_chat', methods=["GET", "POST"])
def further_predict_chat():
    """
    Route to handle further prediction interactions in a chat interface.

    This route retrieves the previous prediction result and related conversation context from the session.
    If a new POST request is made, it processes the user's question and gets a further response based on 
    the previous context and prediction. The new response is then stored in the session and sent back to 
    the user in JSON format.

    Returns:
    jsonify: A JSON response containing the prediction response for the user's question.
    """

    # Retrieve previous prediction and conversation context from session
    pred = session.get("pred", None)
    bot_predict_prompt = session.get("bot_predict_prompt", None)
    bot_predict_response = session.get("bot_predict_response", None)

    # Process new question and get further response if method is POST
    if request.method == 'POST':
        predict_question = request.form['question']

        # Get further response based on the new question and previous context
        predict_prompt, predict_response = get_further_response(prediction=pred, question=predict_question,
                                                                prev_prompt=bot_predict_prompt, prev_response=bot_predict_response)

        # Update session with new response and prompt
        session["bot_predict_response"] = predict_response
        session["bot_predict_prompt"] = predict_question

    # Return the new response in JSON format
    return jsonify({"response": predict_response })






@app.route('/business_idea', methods=["GET", "POST"])
def business_idea():
    """
    Route to handle business idea suggestions based on user inputs.

    This route processes the form data submitted by the user, including their interest in business
    location, financial status (capital or loan), and domain of interest. It then generates a business
    idea prompt and response using these inputs. The user's country and name are also retrieved from the session
    to personalize the response. The response is stored in the session and displayed on the 'chat_business.html' template.

    Returns:
    render_template: Renders the 'chat_business.html' template with business idea response and user details.
    """

    # Extract form data
    country_interest = request.form['country_interest'].capitalize()
    capital_loan = request.form['capital_loan']
    amount = request.form['amount']
    domain_interest = request.form['domain_interest']
    loan_pay_month = request.form['loan_pay_month']

    # Retrieve user's country and name from session
    country = session.get("country", None)
    name = session.get("name", None)

    # Generate business idea prompt and response
    bot_business_prompt, bot_business_response = get_business_idea(country=country,
                                                                   country_interest=country_interest,
                                                                   capital_loan=capital_loan,
                                                                   amount=amount,
                                                                   domain_interest=domain_interest,
                                                                   loan_pay_month=loan_pay_month)

    # Convert the response to JSON format
    bot_business_response = json.loads(bot_business_response)

    # Store business idea response in session
    session["bot_business_response"] = bot_business_response
    session["bot_business_prompt"] = bot_business_prompt

    # Render the business idea page with necessary information
    return render_template('chat_business.html', name=name, country=country, bot_business_response=bot_business_response)






@app.route('/further_business_chat', methods=["GET", "POST"])
def further_business_chat():
    """
    Route to handle further interactions in the business chat interface.

    This route retrieves the previous business chat response and related conversation context from the session.
    If a new POST request is made, it processes the user's question and gets a further response based on 
    the previous context. The new response is then stored in the session and sent back to the user in JSON format.

    Returns:
    jsonify: A JSON response containing the further response for the user's business-related question.
    """

    # Retrieve previous business chat response and prompt from session
    bot_business_response = session.get("bot_business_response", None)
    bot_business_prompt = session.get("bot_business_prompt", None)

    # Process new question and get further response if method is POST
    if request.method == 'POST':
        business_question = request.form['question']

        # Get further response based on the new question and previous context
        business_prompt, business_response = get_further_response(prediction="", question=business_question,
                                                                  prev_prompt=bot_business_prompt, prev_response=bot_business_response)

        # Update session with new response and prompt
        session["bot_business_response"] = business_response
        session["bot_business_prompt"] = business_question

    # Return the new response in JSON format
    return jsonify({"response": business_response })
       




@app.route('/financial_advice', methods=["GET", "POST"])
def financial_advice():
    """
    Route to handle financial advice requests based on user inputs.

    This route processes the form data submitted by the user, including their financial status 
    (capital or loan), business description, and domain of interest. It then generates a financial 
    advice prompt and response using these inputs. The user's country and name are also retrieved from 
    the session to personalize the response. The response is stored in the session and displayed on 
    the 'chat_finance.html' template.

    Returns:
    render_template: Renders the 'chat_finance.html' template with financial advice response and user details.
    """

    # Extract form data
    country_interest = request.form['country_interest'].capitalize()
    capital_loan = request.form['capital_loan']
    description = request.form['description']
    amount = request.form['amount']
    domain_interest = request.form['domain_interest']
    loan_pay_month = request.form['loan_pay_month']

    # Retrieve user's country and name from session
    country = session.get("country", None)
    name = session.get("name", None)

    # Generate financial advice prompt and response
    bot_finance_prompt, bot_finance_response = get_financial_advice(country=country,
                                                                    country_interest=country_interest,
                                                                    description=description,
                                                                    capital_loan=capital_loan,
                                                                    amount=amount,
                                                                    domain_interest=domain_interest,
                                                                    loan_pay_month=loan_pay_month)

    # Convert the response to JSON format
    bot_finance_response = json.loads(bot_finance_response)

    # Store financial advice response in session
    session["bot_finance_response"] = bot_finance_response
    session["bot_finance_prompt"] = bot_finance_prompt

    # Render the financial advice page with necessary information
    return render_template('chat_finance.html', name=name, country=country, bot_finance_response=bot_finance_response)






@app.route('/further_finance_chat', methods=["GET", "POST"])
def further_finance_chat():
    """
    Route to handle follow-up interactions in the financial chat interface.

    This route retrieves the previous financial advice response and related conversation context 
    from the session. If a new POST request is made, it processes the user's financial question 
    and gets a further response based on the previous context. The new response is then stored 
    in the session under the correct keys and sent back to the user in JSON format.

    Returns:
    jsonify: A JSON response containing the further response for the user's finance-related question.
    """

    # Retrieve previous financial advice response and prompt from session
    bot_finance_response = session.get("bot_finance_response", None)
    bot_finance_prompt = session.get("bot_finance_prompt", None)

    # Process new question and get further response if method is POST
    if request.method == 'POST':
        finance_question = request.form['question']

        # Get further response based on the new question and previous context
        finance_prompt, finance_response = get_further_response(prediction="", question=finance_question,
                                                                prev_prompt=bot_finance_prompt, prev_response=bot_finance_response)

        # Update session with new response and prompt
        session["bot_finance_response"] = finance_response
        session["bot_finance_prompt"] = finance_question

    # Return the new response in JSON format
    return jsonify({"response": finance_response })



if __name__ == '__main__':
    app.run(debug= True, use_reloader=False)
