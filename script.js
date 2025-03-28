// script.js (enhanced version)
async function searchResumes() {
    const query = document.getElementById("jobQuery").value.trim();
    if (!query) {
        alert("Please enter a job description.");
        return;
    }

    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = "<p>Searching... ⏳</p>";

    try {
        const response = await fetch(
            `http://127.0.0.1:8000/search?job_description=${encodeURIComponent(query)}`
        );
        
        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);
    } catch (error) {
        resultsDiv.innerHTML = `
            <div class="error">
                <p>❌ Error: ${error.message}</p>
                <p>Please check the console for details.</p>
            </div>
        `;
        console.error("Search error:", error);
    }
}

function displayResults(data) {
    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = "<h3>Matching Resumes:</h3>";

    if (!data.results || data.results.length === 0) {
        resultsDiv.innerHTML += "<p>No matching resumes found.</p>";
        return;
    }

    data.results.forEach((resume, index) => {
        const previewText = resume.text.length > 200 
            ? `${resume.text.substring(0, 200)}...` 
            : resume.text;
        
        resultsDiv.innerHTML += `
            <div class="resume-result">
                <h4>${resume.filename.replace(/.pdf$/i, '')}</h4>
                <p><strong>Category:</strong> ${resume.category || 'N/A'}</p>
                <p><strong>Match:</strong> ${(resume.score * 100).toFixed(1)}%</p>
                <div class="text-preview">${previewText}</div>
                <a href="${resume.file_path}" target="_blank" class="pdf-link">📄 View PDF</a>
                <hr>
            </div>
        `;
    });
}