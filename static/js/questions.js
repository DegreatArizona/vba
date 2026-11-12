const generalQuestions = document.querySelector(".general-questions");
const driverQuestions = document.querySelector(".driver-questions");
const mechanicQuestions = document.querySelector(".mechanic-questions");
const paymentQuestions = document.querySelector(".payment-questions");
const safetyQuestions = document.querySelector(".safety-questions");
const otherQuestions = document.querySelector(".other-questions");

// General Question Array
const generalQuestionArray = [
  {
    question: "What is AutoAid?",
    answer:
      "AutoAid is an innovative platform that connects drivers with nearby mechanics and roadside assistance providers in real-time, ensuring quick and reliable support for vehicle breakdowns anywhere, anytime.",
  },
  {
    question: "How does AutoAid work?",
    answer:
      "Drivers can register on the platform, input their location, and describe their vehicle issues. AutoAid then matches them with the closest qualified mechanic or service provider to assist them.",
  },
  {
    question: "Is AutoAid available 24/7?",
    answer:
      "Yes, AutoAid operates round-the-clock to provide reliable roadside assistance at any time of the day or night.",
  },
  {
    question: "Where is AutoAid currently available?",
    answer:
      "AutoAid is currently operational in [insert specific regions/countries], with plans to expand to more areas soon.",
  },
  {
    question: "Can I track the mechanic in real-time?",
    answer:
      "Absolutely. The platform provides real-time GPS tracking to show the mechanic’s location and estimated arrival time.",
  },
  {
    question: "What happens if there’s a problem with the mechanic’s service?",
    answer:
      "Contact AutoAid support immediately, and we’ll mediate to resolve any issues, including refunds or alternative assistance.",
  },
  {
    question: "Can I cancel or reschedule a service request?",
    answer:
      "Yes, cancellations and rescheduling are allowed under certain conditions. Fees may apply for late cancellations.",
  },
  {
    question: "How do I leave feedback about my experience?",
    answer:
      "After each service, you’ll receive a prompt to rate and review the mechanic via the platform.",
  },
  {
    question: "Does AutoAid have a mobile app?",
    answer:
      "Yes, AutoAid offers a mobile app for iOS and Android to make requesting assistance even easier.",
  },
  {
    question: "Does AutoAid offer corporate or fleet solutions?",
    answer:
      "Yes, we offer tailored solutions for businesses managing vehicle fleets. Contact us for more details.",
  },
  {
    question: "Does AutoAid support electric vehicles (EVs)?",
    answer:
      "Yes, AutoAid has mechanics trained to assist with electric vehicles, including charging support and specialized repairs.",
  },
];

// Driver Question Array
const driverQuestionArray = [
  {
    question: "What types of services does AutoAid offer drivers?",
    answer:
      "AutoAid provides various services, including tire changes, towing, battery jumpstarts, fuel delivery, and on-site mechanical repairs.",
  },
  {
    question: "How do I register as a driver on AutoAid?",
    answer:
      "Simply visit our website, create an account, and fill out your vehicle details. Once registered, you can start using our services.",
  },
  {
    question: "What happens if no mechanic is available near me?",
    answer:
      "If no mechanic is immediately available, AutoAid will notify you and provide an estimated time when assistance can reach you.",
  },
  {
    question: "Is there a membership fee for drivers?",
    answer:
      "AutoAid offers both free and premium membership options. Premium members get priority assistance and discounts on services.",
  },
  {
    question: "Can I request a specific mechanic?",
    answer:
      "Yes, if you’ve previously worked with a mechanic through AutoAid, you can mark them as preferred for future requests.",
  },
];

// Mechanic Question Array
const mechanicQuestionArray = [
  {
    question: "How can I join AutoAid as a mechanic?",
    answer:
      "Mechanics can join by registering on the platform, providing their credentials, certifications, and areas of expertise for verification.",
  },
  {
    question: "What benefits do mechanics get by joining AutoAid?",
    answer:
      "Mechanics gain access to a larger customer base, real-time job requests, and tools to track earnings and reviews.",
  },
  {
    question: "How are mechanics rated on AutoAid?",
    answer:
      "Customers can rate and review mechanics based on their experience, which helps maintain quality and trust on the platform.",
  },
  {
    question: "What percentage does AutoAid take from mechanics' earnings?",
    answer:
      "AutoAid takes a small service fee per job completed, detailed during the onboarding process.",
  },
  {
    question: "Can mechanics set their own rates?",
    answer:
      "Mechanics can suggest rates, but AutoAid also provides recommended pricing to maintain fairness and consistency.",
  },
];

// Payment Question Array
const paymentQuestionArray = [
  {
    question: "How much does it cost to use AutoAid?",
    answer:
      "Costs vary depending on the service requested and location. An estimate is provided before confirming a service request.",
  },
  {
    question: "What payment methods are accepted?",
    answer:
      "AutoAid accepts credit/debit cards, mobile payments, and digital wallets for secure and convenient transactions.",
  },
  {
    question: "Are there additional fees for late-night or urgent requests?",
    answer:
      "Urgent or after-hours requests may incur an additional fee, which will be disclosed during the request process.",
  },
  {
    question: "How are payments processed?",
    answer:
      "Payments are securely processed through AutoAid’s integrated payment gateway. Mechanics receive their payments directly into their accounts.",
  },
];

// Safety Question Array
const safetyQuestionArray = [
  {
    question: "Are AutoAid mechanics vetted?",
    answer:
      "Yes, every mechanic undergoes a rigorous vetting process, including background checks, skill assessments, and customer feedback monitoring.",
  },
  {
    question: "What safety measures are in place for drivers?",
    answer:
      "AutoAid provides detailed mechanic profiles, including photos, ratings, and certifications, ensuring safety and trust.",
  },
  {
    question: "What should I do if I feel unsafe during a service?",
    answer:
      "Contact our support team immediately via the in-app emergency button for assistance.",
  },
  {
    question: "Does AutoAid offer a warranty on services?",
    answer:
      "Warranty terms depend on the service provided and will be detailed in the mechanic’s invoice.",
  },
];

// Other Questions Array
const otherQuestionArray = [
  {
    question: "How can I contact AutoAid for support?",
    answer: `You can reach us via email at <a href="mailto:autoaid7@gmail.com">autoaid7@gmail.com</a>
    <br /><br />
    Or call us on:
    <br />
    <a href="tel:+2348107466823">08107466823</a>
    <br /><br />
    You can visit our branch offices at:
    <br />
    <a href="https://maps.google.com/?q='awka+anambra+state+nigeria'" target="_blank">Awka, Anambra State, Nigeria.</a>`,
  },
];

// General Questions
generalQuestionArray.forEach((item, index) => {
  generalQuestions.innerHTML += `
    <div class="accordion-item">
      <h2 class="accordion-header">
        <button
          class="accordion-button"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#generalQuestion${index}"
          aria-expanded="${index == 0 ? true : false}"
          aria-controls="generalQuestion${index}">
          ${item.question}
        </button>
      </h2>
      <div
        id="generalQuestion${index}"
        class="accordion-collapse collapse ${index == 0 ? "show" : ""}"
        data-bs-parent="#chatAccordion">
        <div class="accordion-body">
          <p class="answer">
            ${item.answer}
          </p>
          <div class="controls">
            <button type="button" class="speak-btn">
              <i class="fa fa-microphone"></i>
            </button>
          </div>
        </div>
      </div>
    </div>`;
});

// Driver Questions
driverQuestionArray.forEach((item, index) => {
  driverQuestions.innerHTML += `
    <div class="accordion-item">
      <h2 class="accordion-header">
        <button
          class="accordion-button"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#driverQuestion${index}"
          aria-expanded="${index == 0 ? true : false}"
          aria-controls="driverQuestion${index}">
          ${item.question}
        </button>
      </h2>
      <div
        id="driverQuestion${index}"
        class="accordion-collapse collapse ${index == 0 ? "show" : ""}"
        data-bs-parent="#chatAccordion">
        <div class="accordion-body">
          <p class="answer">
           ${item.answer}
          </p>
          <div class="controls">
            <button type="button" class="speak-btn">
              <i class="fa fa-microphone"></i>
            </button>
          </div>
        </div>
      </div>
    </div>`;
});

// MechanicQuestions
mechanicQuestionArray.forEach((item, index) => {
  mechanicQuestions.innerHTML += `
    <div class="accordion-item">
      <h2 class="accordion-header">
        <button
          class="accordion-button"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#mechanicQuestion${index}"
          aria-expanded="${index == 0 ? true : false}"
          aria-controls="mechanicQuestion${index}">
          ${item.question}
        </button>
      </h2>
      <div
        id="mechanicQuestion${index}"
        class="accordion-collapse collapse ${index == 0 ? "show" : ""}"
        data-bs-parent="#chatAccordion">
        <div class="accordion-body">
          <p class="answer">
           ${item.answer}
          </p>
          <div class="controls">
            <button type="button" class="speak-btn">
              <i class="fa fa-microphone"></i>
            </button>
          </div>
        </div>
      </div>
    </div>`;
});

// Payment Questions
paymentQuestionArray.forEach((item, index) => {
  paymentQuestions.innerHTML += `
    <div class="accordion-item">
      <h2 class="accordion-header">
        <button
          class="accordion-button"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#paymentQuestion${index}"
          aria-expanded="${index == 0 ? true : false}"
          aria-controls="paymentQuestion${index}">
          ${item.question}
        </button>
      </h2>
      <div
        id="paymentQuestion${index}"
        class="accordion-collapse collapse ${index == 0 ? "show" : ""}"
        data-bs-parent="#chatAccordion">
        <div class="accordion-body">
          <p class="answer">
           ${item.answer}
          </p>
          <div class="controls">
            <button type="button" class="speak-btn">
              <i class="fa fa-microphone"></i>
            </button>
          </div>
        </div>
      </div>
    </div>`;
});

// Safety Questions
safetyQuestionArray.forEach((item, index) => {
  safetyQuestions.innerHTML += `
    <div class="accordion-item">
      <h2 class="accordion-header">
        <button
          class="accordion-button"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#safetyQuestion${index}"
          aria-expanded="${index == 0 ? true : false}"
          aria-controls="safetyQuestion${index}">
          ${item.question}
        </button>
      </h2>
      <div
        id="safetyQuestion${index}"
        class="accordion-collapse collapse ${index == 0 ? "show" : ""}"
        data-bs-parent="#chatAccordion">
        <div class="accordion-body">
          <p class="answer">
           ${item.answer}
          </p>
          <div class="controls">
            <button type="button" class="speak-btn">
              <i class="fa fa-microphone"></i>
            </button>
          </div>
        </div>
      </div>
    </div>`;
});

// Other Questions
otherQuestionArray.forEach((item, index) => {
  otherQuestions.innerHTML += `
    <div class="accordion-item">
      <h2 class="accordion-header">
        <button
          class="accordion-button"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#otherQuestion${index}"
          aria-expanded="${index == 0 ? true : false}"
          aria-controls="otherQuestion${index}">
          ${item.question}
        </button>
      </h2>
      <div
        id="otherQuestion${index}"
        class="accordion-collapse collapse ${index == 0 ? "show" : ""}"
        data-bs-parent="#chatAccordion">
        <div class="accordion-body">
          <p class="answer">
           ${item.answer}
          </p>
          <div class="controls">
            <button type="button" class="speak-btn">
              <i class="fa fa-microphone"></i>
            </button>
          </div>
        </div>
      </div>
    </div>`;
});
