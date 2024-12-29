const express = require('express');
const mongoose = require('mongoose');
const bodyParser = require('body-parser');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const app = express();
const port = 3000;

// MongoDB Atlas connection
mongoose.connect('mongodb+srv://chahidhamdaoui:hamdaoui1@cluster0.kezbfis.mongodb.net/?retryWrites=true&w=majority', { useNewUrlParser: true, useUnifiedTopology: true });

// User schema and model
const userSchema = new mongoose.Schema({
    username: String,
    email: String,
    password: String,
    balance: { type: Number, default: 0 }
});
const User = mongoose.model('User', userSchema);

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Register endpoint
app.post('/api/register', async (req, res) => {
    const { username, email, password } = req.body;
    const hashedPassword = await bcrypt.hash(password, 10);
    const user = new User({ username, email, password: hashedPassword });
    await user.save();
    res.json({ success: true });
});

// Login endpoint
app.post('/api/login', async (req, res) => {
    const { username, password } = req.body;
    const user = await User.findOne({ username });
    if (user && await bcrypt.compare(password, user.password)) {
        const token = jwt.sign({ userId: user._id }, 'your_jwt_secret');
        res.json({ success: true, token });
    } else {
        res.json({ success: false, message: 'Invalid credentials' });
    }
});

// Middleware to authenticate token
const authenticateToken = (req, res, next) => {
    const token = req.headers['authorization'];
    if (!token) return res.sendStatus(401);
    jwt.verify(token, 'your_jwt_secret', (err, user) => {
        if (err) return res.sendStatus(403);
        req.user = user;
        next();
    });
};

// Get user data endpoint
app.get('/api/user/:id', authenticateToken, async (req, res) => {
    const user = await User.findById(req.params.id);
    res.json(user);
});

// Top up balance endpoint
app.post('/api/top-up', authenticateToken, async (req, res) => {
    const { userId, amount } = req.body;
    const user = await User.findById(userId);
    user.balance += amount;
    await user.save();
    res.json({ newBalance: user.balance });
});

// Place order endpoint
app.post('/api/order', authenticateToken, async (req, res) => {
    const { userId, pickupTime } = req.body;
    const user = await User.findById(userId);
    const orderCost = 10; // Example cost
    if (user.balance >= orderCost) {
        user.balance -= orderCost;
        await user.save();
        res.json({ success: true, newBalance: user.balance });
    } else {
        res.json({ success: false, message: 'Insufficient balance' });
    }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
