const chatBotBtn = document.querySelector(".chat-bot-btn");
const chatBotContainer = document.querySelector(".chat-bot-container");
const chatBotBody = document.querySelector(".chat-bot-body");
const chatBotFooter = document.querySelector(".chat-bot-footer");
const questionCategories = document.querySelectorAll(".question-category");
const questionCategoryBtns = document.querySelectorAll(
  ".question-category-btn"
);

// hide or show questions
chatBotBtn.addEventListener("click", () => {
  chatBotContainer.classList.toggle("hide");
});

// toggle question categories
document
  .querySelectorAll(".question-category-btn, .question-category-btn i")
  .forEach((element) => {
    element.addEventListener("click", (event) => {
      const target = event.target.closest(".question-category-btn");
      if (target) {
        questionCategoryBtns.forEach((categoryBtn) => {
          categoryBtn.classList.remove("active");
        });
        target.classList.add("active");
        questionCategories.forEach((category) => {
          category.classList.remove("show");
        });
        document.querySelector(`.${target.id}-questions`).classList.add("show");
      }
    });
  });

// Speech Synthesis
const speakBtns = document.querySelectorAll(".chat-bot .speak-btn");
let speech = new SpeechSynthesisUtterance();
speech.rate = 0.7; // the speed of speecch

let voices = [];
let voiceSelect = document.querySelector("#voice");

window.speechSynthesis.onvoiceschanged = () => {
  voices = window.speechSynthesis.getVoices();
  speech.voice = voices[0];

  voices.forEach(
    (voice, i) => (voiceSelect.options[i] = new Option(voice.name, i))
  );
};

voiceSelect.addEventListener("change", () => {
  speech.voice = voices[voiceSelect.value];
  voiceSelect.classList.remove("show");
});
voiceSelect.addEventListener("blur", () => {
  voiceSelect.classList.remove("show");
});

speakBtns.forEach((speakBtn) => {
  speakBtn.onclick = () => {
    const paragraph = speakBtn.parentElement.previousElementSibling;
    speech.text = paragraph.innerText;
    window.speechSynthesis.speak(speech);
  };
});

// show voices options
const triggerBtn = document.getElementById("trigger-select");
triggerBtn.addEventListener("click", () =>
  voiceSelect.classList.toggle("show")
);
