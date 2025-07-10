PRD:

- upload CAS file button
- if file is not uploaded, the chatbot should answer generic questions, but ask the user to upload file timely
- once file is uploaded, it should show a success(or failure) message in history
- after file is uploaded successfuly, show portfolio holdings, and tell the user to ask questions with examples
- multi-session chat
- show ASCII charts wherever make sense

- type of questions that can be asked
    + portfolio summary
    + total investment and gain/loss
    + which fund has performed the best and worst in terms of xirr and absolute
    + sorted list of funds as per their performance xirr and absolute
    + 
    + show cap composition
    + returns per cap
    + funds in a given cap with their returns
    + ideal cap composition as per user's age
    + what is my xirr in large-cap funds?
    + realised gains and unrealised gains
    +
    + multi lingual support


TDD:

- streamlit for cas upload and chat bot
- fastapi for backend (POST /api/chat)
- implement codeAgent for most calculations
- [x] assign a UUID for a session isolation
- save session messages in some store


PMD:

- generate session uuid and send it in every request
- file upload
- chatbot questions
