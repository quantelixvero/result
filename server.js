const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// Catch-all 301 Redirect for SEO and traffic migration
// Using 301 (Permanent) is critical for transferring Google search rankings.
app.use((req, res) => {
    const newDomain = 'https://thedcarchive.pages.dev';
    console.log(`[MIGRATION LOG] ${new Date().toISOString()} - Redirecting ${req.method} ${req.url} -> ${newDomain}`);
    
    // Redirect all paths to the home page of the new domain
    res.redirect(301, `${newDomain}/`);
});

app.listen(PORT, () => {
    console.log('------------------------------------------------------------');
    console.log('MIGRATION SERVER RUNNING');
    console.log(`Listening on port ${PORT}`);
    console.log('Redirecting all traffic (301) to: https://thedcarchive.pages.dev/');
    console.log('------------------------------------------------------------');
});
