# [React Flask LLM Application]

A full-stack LLM project that uses a `React UI` powered by a simple `Flask API Server`. 
<br />

## ✨ **Start the Flask API** 

```bash
$ cd llm-test
$ cd flask-server
$ pip install -r requirement.txt #Make sure to install any extra modules in requirment.txt
```

At this point, the API should be up & running at `http://localhost:5000`, and we can test the interface using POSTMAN or `curl`.

<br />

## ✨ **Start the React UI** (use another terminal)

> 👉 **Step 1** - Once the project is downloaded, change the directory to `react-ui`. 

```bash
$cd llm-test
$ cd react-ui
#look for instructions on how to install npm in the readme file insdie 'client' folder
```

<br >

> 👉 **Step 2** - Install dependencies via NPM or yarn

```bash
$ npm i
// OR
$ yarn
```

<br />

> 👉 **Step 3** - Start in development mode

```bash
$ npm run start 
// OR
$ yarn start
```

Once all the above commands are executed, the `React UI` should be visible in the browser. By default, the app redirects the guest users to authenticate. 
After we register a new user and signIN, all the private pages become accessible. 

<br />

## ✨ General Information

The product is built using React as a frontend component that accepts a pdf and a use question which is then processed in the Flask backend using LangchainAI API:

- `Compile and start` the **Flask API Backend**
  - be default the server starts on port `5000`
- `Compile and start` the **React UI**
  - UI will start on port `3000` and expects a running backend on port `5000`
- `Configuration` (Optional)
  - Change the API port
  - Configure the API port used by the React UI to communicate with the backend 

<br />

## ✨ Manual build

> 👉 **Start the Flask API** 

```bash
$ cd llm-test
$ cd flask-server
$ 
$ # Create a virtual environment
$ virtualenv env
$ source env/bin/activate
$
$ # Install modules
$ pip install -r requirement.txt #make sure to install any extra library if there are errors
$
$ # Set Up the Environment
$ export FLASK_APP=run.py
$ export FLASK_ENV=development
$ 
$ # Start the API
$ flask run  | $ python3 server.py
```

<br />

> 👉 **Compile & start the React UI**

```bash
$ cd llm-test
$ cd client
$
$ # Install Modules
$ yarn | $ npm install
$
$ # Start for development (LIVE Reload)
$ yarn start  | $ npm run start
```

<br />

