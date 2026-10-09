function search(path) {
    var xhr = new XMLHttpRequest();

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            console.log("Search results received:" + xhr.responseText);
            eval("var searchResultsObj = " + xhr.responseText);
            
            renderResults(searchResultsObj);
        }
    };

    xhr.open("GET",  path +  window.location.search, true);
    console.log("Request prepared." + path);
    console.log("Sending request to: " + path  + window.location.search);
    xhr.send();

function renderResults(data) {
    const blogHeader = document.querySelector(".blog-header");
    const posts = document.querySelectorAll(".archives .post");

    // Reset header
    blogHeader.innerHTML = "";

    let count = 0;

    posts.forEach(post => {
        const title = post.querySelector("h2")?.innerText || "";
        const body = post.querySelector("p")?.innerText || "";

        const haystack = (title + " " + body).toLowerCase();
        const needle = data.searchTerm.toLowerCase();

        if (haystack.includes(needle)) {
            post.style.display = "block";
            count++;
        } else {
            post.style.display = "none";
        }
    });

    // Header text
    const h1 = document.createElement("h1");
    h1.innerText =
        count +
        " fragments found in the Archives of Constantinople for '" +
        data.searchTerm +
        "'";
    blogHeader.appendChild(h1);

    blogHeader.appendChild(document.createElement("hr"));
}

}
