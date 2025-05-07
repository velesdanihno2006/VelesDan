require('dotenv').config();
const TelegramBot = require('node-telegram-bot-api');
const questions = require('./questions');
const fs = require('fs');

const token = process.env.TELEGRAM_BOT_TOKEN;
const bot = new TelegramBot(token, {polling: true});

let users = {};

try {
    const data = fs.readFileSync('./users.json', 'utf8');
    users = JSON.parse(data);
    for (const userId in users) {
        if (!users[userId].incorrectQuestions) {
            users[userId].incorrectQuestions = [];
        }
    }
} catch (err) {
    console.log('No users file found, starting fresh');
}

function saveUsers() {
    fs.writeFileSync('./users.json', JSON.stringify(users, null, 2));
}

function getMainMenuKeyboard() {
    return {
        reply_markup: {
            keyboard: [
                [{text: '🚀 Начать викторину'}],
                [{text: '📊 Моя статистика'}, {text: '🆘 Помощь'}]
            ],
            resize_keyboard: true
        }
    };
}

function getAnswerKeyboard() {
    return {
        reply_markup: {
            keyboard: [
                [{text: 'а'}, {text: 'б'}, {text: 'в'}],
                [{text: 'Пропустить вопрос'}, {text: '◀️ Главное меню'}]
            ],
            resize_keyboard: true
        }
    };
}

function getFinalMenuKeyboard() {
    return {
        reply_markup: {
            keyboard: [
                [{text: '🔁 Повторить ошибки'}, {text: '🔄 Начать заново'}],
                [{text: '◀️ Главное меню'}]
            ],
            resize_keyboard: true
        }
    };
}

function getStatsKeyboard() {
    return {
        reply_markup: {
            keyboard: [
                [{text: '🚀 Начать викторину'}, {text: '🆘 Помощь'}],
                [{text: '🗑️ Сбросить статистику'}, {text: '◀️ Главное меню'}]
            ],
            resize_keyboard: true
        }
    };
}

bot.onText(/\/start/, (msg) => {
    const chatId = msg.chat.id;
    const userId = msg.from.id;

    if (!users[userId]) {
        users[userId] = {
            correct: 0,
            incorrect: 0,
            skipped: 0,
            answers: {},
            incorrectQuestions: [],
            currentQuestion: null,
            repeatingIncorrect: null,
            repeatMode: false,
            repeatCorrect: 0,
            repeatIncorrect: 0,
            repeatSkipped: 0
        };
        saveUsers();
    }

    const welcomeMessage = `
    🌟 *Добро пожаловать в BMW Knowledge Quiz!* 🌟

🚗 *Прокачай свои знания о BMW!* 🚗

Этот бот поможет вам:
• Углубить знания о моделях и технологиях BMW
• Подготовиться к работе с клиентами
• Узнать интересные технические детали
• Повысить свою экспертизу в игровой форме

📚 *Как это работает:*
1. Вы отвечаете на вопросы викторины
2. Получаете объяснения к каждому ответу
3. Анализируете свои ошибки
4. Улучшаете результат с каждым прохождением

🔹 *Почему это полезно:*
✔ Лучше понимаете продукт BMW
✔ Можете увереннее общаться с клиентами
✔ Повышаете свою профессиональную ценность
`;
    bot.sendMessage(chatId, welcomeMessage, {
        parse_mode: 'Markdown',
        ...getMainMenuKeyboard()
    });
});

bot.on('message', (msg) => {
    const chatId = msg.chat.id;
    const userId = msg.from.id;
    const text = msg.text;

    if (!users[userId]) {
        bot.sendMessage(chatId, 'Пожалуйста, сначала нажмите /start');
        return;
    }

    switch(text) {
        case '🚀 Начать викторину':
            startQuiz(chatId, userId);
            break;
        case '📊 Моя статистика':
            showStats(chatId, userId);
            break;
        case '🆘 Помощь':
            showHelp(chatId);
            break;
        case '➡️ Следующий вопрос':
            if (users[userId].repeatMode) {
                askNextIncorrectQuestion(chatId, userId);
            } else {
                askQuestion(chatId, userId);
            }
            break;
        case '🔄 Начать заново':
            resetQuiz(chatId, userId);
            break;
        case '🔁 Повторить ошибки':
            repeatIncorrectQuestions(chatId, userId);
            break;
        case 'Пропустить вопрос':
            skipQuestion(chatId, userId);
            break;
        case '🗑️ Сбросить статистику':
            resetStats(chatId, userId);
            break;
        case '◀️ Главное меню':
            const welcomeMessage = `
🌟 *Добро пожаловать в BMW Knowledge Quiz!* 🌟

🚗 *Прокачай свои знания о BMW!* 🚗

Этот бот поможет вам:
• Углубить знания о моделях и технологиях BMW
• Подготовиться к работе с клиентами
• Узнать интересные технические детали
• Повысить свою экспертизу в игровой форме

📚 *Как это работает:*
1. Вы отвечаете на вопросы викторины
2. Получаете объяснения к каждому ответу
3. Анализируете свои ошибки
4. Улучшаете результат с каждым прохождением

🔹 *Почему это полезно:*
✔ Лучше понимаете продукт BMW
✔ Можете увереннее общаться с клиентами
✔ Повышаете свою профессиональную ценность
`;
            bot.sendMessage(chatId, welcomeMessage, {
                parse_mode: 'Markdown',
                ...getMainMenuKeyboard()
            });
            break;
        case 'а':
        case 'б':
        case 'в':
            handleAnswer(chatId, userId, text);
            break;
        default:
            if (msg.text && msg.text.startsWith('/')) return;
            bot.sendMessage(chatId, 'Пожалуйста, используйте кнопки для навигации', getMainMenuKeyboard());
    }
});

function startQuiz(chatId, userId) {
    const user = users[userId];
    user.answers = {};
    user.correct = 0;
    user.incorrect = 0;
    user.skipped = 0;
    user.incorrectQuestions = [];
    user.currentQuestion = null;
    user.repeatingIncorrect = null;
    user.repeatMode = false;
    saveUsers();

    askQuestion(chatId, userId);
}

function resetQuiz(chatId, userId) {
    const user = users[userId];
    user.answers = {};
    user.correct = 0;
    user.incorrect = 0;
    user.skipped = 0;
    user.incorrectQuestions = [];
    user.currentQuestion = null;
    user.repeatingIncorrect = null;
    user.repeatMode = false;
    saveUsers();

    bot.sendMessage(chatId, 'Викторина начата заново! Все предыдущие ответы очищены.');
    askQuestion(chatId, userId);
}

function resetStats(chatId, userId) {
    const user = users[userId];
    user.correct = 0;
    user.incorrect = 0;
    user.skipped = 0;
    user.incorrectQuestions = [];
    saveUsers();

    bot.sendMessage(chatId, '📊 Ваша статистика была сброшена!', getStatsKeyboard());
}

function repeatIncorrectQuestions(chatId, userId) {
    const user = users[userId];

    if (!user.incorrectQuestions || user.incorrectQuestions.length === 0) {
        bot.sendMessage(chatId, 'У вас нет вопросов с ошибками для повторения!', getMainMenuKeyboard());
        return;
    }

    user.repeatingIncorrect = [...user.incorrectQuestions];
    user.repeatMode = true;
    user.repeatCorrect = 0;
    user.repeatIncorrect = 0;
    user.repeatSkipped = 0;
    saveUsers();

    askNextIncorrectQuestion(chatId, userId);
}

function askNextIncorrectQuestion(chatId, userId) {
    const user = users[userId];

    if (!user.repeatingIncorrect || user.repeatingIncorrect.length === 0) {
        const total = user.repeatCorrect + user.repeatIncorrect + user.repeatSkipped;
        const percentage = total > 0 ? Math.round((user.repeatCorrect / total) * 100) : 0;

        let resultMessage = `🔁 *Повторение ошибок завершено!*\n\n` +
            `📊 *Результаты повторения:*\n` +
            `✅ Правильных: ${user.repeatCorrect}\n` +
            `❌ Неправильных: ${user.repeatIncorrect}\n` +
            `⏩ Пропущено: ${user.repeatSkipped}\n` +
            `📈 Процент правильных: ${percentage}%\n\n`;

        user.incorrectQuestions = user.repeatingIncorrect;
        user.repeatingIncorrect = null;
        user.repeatMode = false;
        saveUsers();

        if (user.incorrectQuestions.length > 0) {
            resultMessage += `📌 У вас остались вопросы с ошибками. Вы можете повторить их снова.`;
        } else {
            resultMessage += `🎉 Поздравляем! Вы исправили все ошибки!`;
        }

        bot.sendMessage(chatId, resultMessage, {
            parse_mode: 'Markdown',
            ...getFinalMenuKeyboard()
        });
        return;
    }

    const questionId = user.repeatingIncorrect[0];
    const question = questions.find(q => q.id === questionId);

    if (!question) {
        user.repeatingIncorrect.shift();
        askNextIncorrectQuestion(chatId, userId);
        return;
    }

    user.currentQuestion = question.id;

    const currentIndex = user.incorrectQuestions.length - user.repeatingIncorrect.length + 1;
    let questionText = `🔁 *Повторение ошибок (${currentIndex}/${user.incorrectQuestions.length}):*\n\n` +
        `❓ ${question.text}\n\n`;
    question.options.forEach((opt, i) => {
        const letter = String.fromCharCode(1072 + i);
        questionText += `*${letter})* ${opt.text}\n`;
    });

    bot.sendMessage(chatId, questionText, {
        parse_mode: 'Markdown',
        ...getAnswerKeyboard()
    });
}

function skipQuestion(chatId, userId) {
    const user = users[userId];
    if (!user || !user.currentQuestion) {
        bot.sendMessage(chatId, 'Нет активного вопроса для пропуска');
        return;
    }

    const question = questions.find(q => q.id === user.currentQuestion);
    if (!question) {
        bot.sendMessage(chatId, 'Ошибка: вопрос не найден');
        return;
    }

    const sendNextQuestion = () => {
        if (user.repeatMode) {
            askNextIncorrectQuestion(chatId, userId);
        } else {
            const unansweredQuestions = questions.filter(q => user.answers[q.id] === undefined);
            if (unansweredQuestions.length === 0) {
                showFinalResults(chatId, userId);
            } else {
                askQuestion(chatId, userId);
            }
        }
    };

    if (user.repeatMode) {
        user.repeatSkipped++;
        user.repeatingIncorrect = user.repeatingIncorrect.filter(id => id !== question.id);
        user.repeatingIncorrect.push(question.id);
    } else {
        user.skipped++;
        user.answers[question.id] = null;

        if (!user.incorrectQuestions) user.incorrectQuestions = [];
        if (!user.incorrectQuestions.includes(question.id)) {
            user.incorrectQuestions.push(question.id);
        }
    }

    const correctOption = question.options.find(opt => opt.correct);
    bot.sendMessage(chatId,
        `⏩ Вопрос пропущен!\n` +
        `✅ Правильный ответ: ${correctOption.text}\n\n` +
        question.explanation,
        {parse_mode: 'Markdown'}
    ).then(sendNextQuestion);

    saveUsers();
}

function askQuestion(chatId, userId) {
    const user = users[userId];
    const unansweredQuestions = questions.filter(q => user.answers[q.id] === undefined);

    if (unansweredQuestions.length === 0) {
        showFinalResults(chatId, userId);
        return;
    }

    const randomIndex = Math.floor(Math.random() * unansweredQuestions.length);
    const question = unansweredQuestions[randomIndex];
    user.currentQuestion = question.id;

    const answeredCount = questions.length - unansweredQuestions.length;
    let questionText = `❓ *Вопрос ${answeredCount + 1}/${questions.length}:* ${question.text}\n\n`;
    question.options.forEach((opt, i) => {
        const letter = String.fromCharCode(1072 + i);
        questionText += `*${letter})* ${opt.text}\n`;
    });

    bot.sendMessage(chatId, questionText, {
        parse_mode: 'Markdown',
        ...getAnswerKeyboard()
    });
}

function handleAnswer(chatId, userId, answerLetter) {
    const user = users[userId];
    if (!user || !user.currentQuestion) {
        bot.sendMessage(chatId, 'Нет активного вопроса для ответа');
        return;
    }

    const question = questions.find(q => q.id === user.currentQuestion);
    if (!question) {
        bot.sendMessage(chatId, 'Ошибка: вопрос не найден');
        return;
    }

    const optionIndex = answerLetter.charCodeAt(0) - 1072;
    if (optionIndex < 0 || optionIndex >= question.options.length) {
        bot.sendMessage(chatId, 'Неверный вариант ответа');
        return;
    }

    const selectedOption = question.options[optionIndex];
    const isCorrect = selectedOption.correct;

    const sendNextQuestion = () => {
        if (user.repeatMode) {
            askNextIncorrectQuestion(chatId, userId);
        } else {
            const unansweredQuestions = questions.filter(q => user.answers[q.id] === undefined);
            if (unansweredQuestions.length === 0) {
                showFinalResults(chatId, userId);
            } else {
                askQuestion(chatId, userId);
            }
        }
    };

    if (user.repeatMode) {
        if (isCorrect) {
            user.repeatCorrect++;
            user.repeatingIncorrect = user.repeatingIncorrect.filter(id => id !== question.id);
            bot.sendMessage(chatId, `✅ *Правильно!*\n${question.explanation}`, {
                parse_mode: 'Markdown'
            }).then(sendNextQuestion);
        } else {
            user.repeatIncorrect++;
            user.repeatingIncorrect = user.repeatingIncorrect.filter(id => id !== question.id);
            user.repeatingIncorrect.push(question.id);

            const correctOption = question.options.find(opt => opt.correct);
            bot.sendMessage(chatId,
                `❌ *Неправильно!*\nВы выбрали: ${selectedOption.text}\n` +
                `✅ Правильный ответ: ${correctOption.text}\n\n` +
                question.explanation,
                {parse_mode: 'Markdown'}
            ).then(sendNextQuestion);
        }
    } else {
        user.answers[question.id] = isCorrect;

        if (isCorrect) {
            user.correct++;
            if (user.incorrectQuestions?.includes(question.id)) {
                user.incorrectQuestions = user.incorrectQuestions.filter(id => id !== question.id);
            }
            bot.sendMessage(chatId, `✅ *Правильно!*\n${question.explanation}`, {
                parse_mode: 'Markdown'
            }).then(sendNextQuestion);
        } else {
            user.incorrect++;
            if (!user.incorrectQuestions) user.incorrectQuestions = [];
            if (!user.incorrectQuestions.includes(question.id)) {
                user.incorrectQuestions.push(question.id);
            }

            const correctOption = question.options.find(opt => opt.correct);
            bot.sendMessage(chatId,
                `❌ *Неправильно!*\nВы выбрали: ${selectedOption.text}\n` +
                `✅ Правильный ответ: ${correctOption.text}\n\n` +
                question.explanation,
                {parse_mode: 'Markdown'}
            ).then(sendNextQuestion);
        }
    }
    saveUsers();
}

function showFinalResults(chatId, userId) {
    const user = users[userId];
    const total = questions.length;
    const percentage = Math.round((user.correct / total) * 100);

    let detailedResults = `📝 *Подробные результаты:*\n\n`;
    questions.forEach((question, index) => {
        const answerStatus = user.answers[question.id];
        const correctOption = question.options.find(opt => opt.correct);

        detailedResults += `${index + 1}. ${question.text}\n`;

        if (answerStatus === null) {
            detailedResults += `   ⏩ Пропущен\n`;
        } else if (answerStatus === true) {
            detailedResults += `   ✅ Правильно\n`;
        } else {
            const selectedOption = question.options.find(opt =>
                user.answers[question.id] === false && opt.text
            );
            detailedResults += `   ❌ Ошибка${selectedOption ? ` (выбрано: ${selectedOption.text})` : ''}\n`;
        }

        detailedResults += `   🔹 Правильный ответ: ${correctOption.text}\n\n`;
    });

    let statsMessage = `🎉 *Викторина завершена!*\n\n` +
        `📊 *Ваши результаты:*\n` +
        `✅ Правильных: ${user.correct}/${total} (${percentage}%)\n` +
        `❌ Неправильных: ${user.incorrect}\n` +
        `⏩ Пропущено: ${user.skipped}\n\n` +
        `${detailedResults}`;

    if (user.incorrectQuestions && user.incorrectQuestions.length > 0) {
        statsMessage += `📌 *Рекомендуем повторить:*\n`;
        user.incorrectQuestions.forEach((qId, index) => {
            const q = questions.find(question => question.id === qId);
            if (q) {
                const qNumber = questions.findIndex(question => question.id === qId) + 1;
                statsMessage += `${index + 1}. [Вопрос ${qNumber}] ${q.text}\n`;
            }
        });
        statsMessage += `\nНажмите "🔁 Повторить ошибки" для работы над ошибками`;
    } else {
        statsMessage += `🎯 Отличный результат! Все ответы правильные!`;
    }

    bot.sendMessage(chatId, statsMessage, {
        parse_mode: 'Markdown',
        ...getFinalMenuKeyboard()
    });
}

function showStats(chatId, userId) {
    const user = users[userId];
    if (!user) {
        bot.sendMessage(chatId, 'Ошибка: пользователь не найден');
        return;
    }

    const totalAnswered = user.correct + user.incorrect + (user.skipped || 0);
    const percentage = totalAnswered > 0 ? Math.round((user.correct / totalAnswered) * 100) : 0;

    const statsMessage = `📊 *Ваша статистика:*\n\n` +
        `✅ Правильных ответов: ${user.correct}\n` +
        `❌ Неправильных ответов: ${user.incorrect}\n` +
        `⏩ Пропущено вопросов: ${user.skipped || 0}\n` +
        `📈 Процент правильных: ${percentage}%`;

    bot.sendMessage(chatId, statsMessage, {
        parse_mode: 'Markdown',
        ...getStatsKeyboard()
    });
}

function showHelp(chatId) {
    const helpMessage = `🛠 *Помощь*\n\n` +
        `Этот бот поможет вам изучить технические характеристики BMW.\n\n` +
        `*Как использовать викторину:*\n` +
        `- Нажмите "🚀 Начать викторину"\n` +
        `- Выбирайте ответы (а, б, в) или пропускайте вопросы\n` +
        `- После ответа вы увидите результат и объяснение\n` +
        `- По окончании получите рекомендации по сложным вопросам\n\n` +
        `*Все команды:*\n` +
        `/start - Главное меню\n` +
        `/quiz - Начать викторину\n` +
        `/stats - Показать статистику\n` +
        `/help - Эта справка`;

    bot.sendMessage(chatId, helpMessage, {
        parse_mode: 'Markdown',
        reply_markup: {
            keyboard: [
                [{text: '🚀 Начать викторину'}],
                [{text: '📊 Моя статистика'},{text: '◀️ Главное меню'}]
            ],
            resize_keyboard: true
        }
    });
}

bot.onText(/\/quiz/, (msg) => startQuiz(msg.chat.id, msg.from.id));
bot.onText(/\/stats/, (msg) => showStats(msg.chat.id, msg.from.id));
bot.onText(/\/help/, (msg) => showHelp(msg.chat.id));

bot.on('polling_error', (error) => {
    console.error('Polling error:', error);
});

console.log('Бот запущен...');