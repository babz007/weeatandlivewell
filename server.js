require('dotenv').config();
const express = require('express');
const passport = require('passport');
const GoogleStrategy = require('passport-google-oauth20').Strategy;
const jwt = require('jsonwebtoken');
const cors = require('cors');
const bodyParser = require('body-parser');
const mysql = require('mysql2/promise');
const bcrypt = require('bcrypt');

const app = express();
app.use(cors());
app.use(bodyParser.json());
app.use(passport.initialize());

// Database connection
const pool = mysql.createPool({
    host: 'localhost',
    user: 'root',
    password: '',
    database: 'weeatandlivewell'
});

// Passport Google Strategy
passport.use(new GoogleStrategy({
    clientID: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    callbackURL: process.env.GOOGLE_CALLBACK_URL
},
async (accessToken, refreshToken, profile, done) => {
    try {
        // Check if user is whitelisted
        const [users] = await pool.query(
            'SELECT * FROM admin_users WHERE email = ? AND is_whitelisted = TRUE',
            [profile.emails[0].value]
        );

        if (users.length === 0) {
            return done(null, false, { message: 'Not authorized' });
        }

        const user = users[0];
        
        // Update or create user
        if (!user.google_id) {
            await pool.query(
                'UPDATE admin_users SET google_id = ?, last_login = CURRENT_TIMESTAMP WHERE id = ?',
                [profile.id, user.id]
            );
        } else {
            await pool.query(
                'UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                [user.id]
            );
        }

        return done(null, user);
    } catch (error) {
        return done(error);
    }
}));

// Regular Login Endpoint
app.post('/api/admin/login', async (req, res) => {
    try {
        const { username, password } = req.body;
        
        // Validate input
        if (!username || !password) {
            return res.status(400).json({ error: 'Username and password are required' });
        }
        
        // Get user from database
        const [users] = await pool.query(
            'SELECT * FROM admin_users WHERE username = ? AND is_active = TRUE',
            [username]
        );
        
        if (users.length === 0) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        
        const user = users[0];
        
        // Verify password
        const isPasswordValid = await bcrypt.compare(password, user.password_hash);
        if (!isPasswordValid) {
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        
        // Update last login
        await pool.query(
            'UPDATE admin_users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
            [user.id]
        );
        
        // Generate JWT token
        const token = jwt.sign(
            { userId: user.id, email: user.email },
            process.env.JWT_SECRET,
            { expiresIn: '24h' }
        );
        
        res.json({ token });
    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Google OAuth Routes
app.get('/api/auth/google',
    passport.authenticate('google', { scope: ['profile', 'email'] })
);

app.get('/api/auth/google/callback',
    passport.authenticate('google', { session: false }),
    async (req, res) => {
        try {
            const token = jwt.sign(
                { userId: req.user.id, email: req.user.email },
                process.env.JWT_SECRET,
                { expiresIn: '24h' }
            );
            
            res.redirect(`/admin.html?token=${token}`);
        } catch (error) {
            res.redirect('/admin.html?error=authentication_failed');
        }
    }
);

// Middleware to verify JWT token
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({ error: 'No token provided' });
    }
    
    jwt.verify(token, process.env.JWT_SECRET, async (err, decoded) => {
        if (err) {
            return res.status(403).json({ error: 'Invalid token' });
        }
        
        // Verify user is still whitelisted
        const [users] = await pool.query(
            'SELECT * FROM admin_users WHERE id = ? AND is_active = TRUE',
            [decoded.userId]
        );
        
        if (users.length === 0) {
            return res.status(403).json({ error: 'User no longer authorized' });
        }
        
        req.user = decoded;
        next();
    });
};

// Admin Dashboard Stats Endpoint
app.get('/api/admin/stats', authenticateToken, async (req, res) => {
    try {
        // Get total posts
        const [postsResult] = await pool.query('SELECT COUNT(*) as total FROM posts');
        const totalPosts = postsResult[0].total;
        
        // Get total comments
        const [commentsResult] = await pool.query('SELECT COUNT(*) as total FROM comments');
        const totalComments = commentsResult[0].total;
        
        // Get total subscribers
        const [subscribersResult] = await pool.query('SELECT COUNT(*) as total FROM subscribers');
        const totalSubscribers = subscribersResult[0].total;
        
        // Get recent posts
        const [recentPosts] = await pool.query(`
            SELECT id, title, date_posted, status 
            FROM posts 
            ORDER BY date_posted DESC 
            LIMIT 10
        `);
        
        res.json({
            totalPosts,
            totalComments,
            totalSubscribers,
            recentPosts
        });
    } catch (error) {
        console.error('Error fetching stats:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

// Whitelist Management Endpoints (protected)
app.post('/api/admin/whitelist', authenticateToken, async (req, res) => {
    try {
        const { email, full_name } = req.body;
        
        await pool.query(
            'INSERT INTO admin_users (email, full_name, is_whitelisted) VALUES (?, ?, TRUE)',
            [email, full_name]
        );
        
        res.json({ message: 'User whitelisted successfully' });
    } catch (error) {
        console.error('Error whitelisting user:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.delete('/api/admin/whitelist/:email', authenticateToken, async (req, res) => {
    try {
        const { email } = req.params;
        
        await pool.query(
            'UPDATE admin_users SET is_whitelisted = FALSE WHERE email = ?',
            [email]
        );
        
        res.json({ message: 'User removed from whitelist' });
    } catch (error) {
        console.error('Error removing user from whitelist:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
}); 