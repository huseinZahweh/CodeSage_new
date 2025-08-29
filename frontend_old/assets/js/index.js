const myinformation = {
    authenticated: false,
    username: "",
    password: ""
}

function Enterpage(page){
    location.href=`${page}.html`
}

document.getElementById("getstartedbtn").onclick = function(){
    if (!myinformation.authenticated){
        Enterpage('./Auth/Signin')
    }else{
        Enterpage('/Problems/problems')
    }
}

// Check if user is authenticated and update UI accordingly
function checkAuthStatus() {
    const storedAuth = localStorage.getItem('codeSageAuth');
    if (storedAuth) {
        const authData = JSON.parse(storedAuth);
        myinformation.authenticated = authData.authenticated;
        myinformation.username = authData.username;
        myinformation.password = authData.password;
    }
    
    updateAuthSection();
}

// Update authentication section in header
function updateAuthSection() {
    const authSection = document.getElementById('authSection');
    if (!authSection) return;
    
    if (myinformation.authenticated) {
        authSection.innerHTML = `
            <div class="profilecontainer" onclick="toggleProfileMenu()">
                <div class="profilepicture">${myinformation.username.charAt(0).toUpperCase()}</div>
                <div class="username">${myinformation.username}</div>
            </div>
            <div class="profilemenu" id="profileMenu">
                <div class="menuitem" onclick="Enterpage('../Profile/profile')">
                    <i class="fas fa-user"></i> Profile
                </div>
                <div class="menuitem" onclick="Enterpage('../Settings/settings')">
                    <i class="fas fa-cog"></i> Settings
                </div>
                <div class="menuitem" onclick="signOut()">
                    <i class="fas fa-sign-out-alt"></i> Sign Out
                </div>
            </div>
        `;
    } else {
        authSection.innerHTML = `
            <div class="signincontainer">
                <button type="button" class="Signinbtn" onclick="Enterpage('../Auth/Signin')">Sign in</button>
            </div>
        `;
    }
}

// Toggle profile menu
function toggleProfileMenu() {
    const profileMenu = document.getElementById('profileMenu');
    if (profileMenu.style.display === 'block') {
        profileMenu.style.display = 'none';
    } else {
        profileMenu.style.display = 'block';
    }
}

// Close profile menu when clicking outside
document.addEventListener('click', function(event) {
    const profileMenu = document.getElementById('profileMenu');
    const profileContainer = document.querySelector('.profilecontainer');
    
    if (profileMenu && profileMenu.style.display === 'block' && 
        !profileMenu.contains(event.target) && 
        !(profileContainer && profileContainer.contains(event.target))) {
        profileMenu.style.display = 'none';
    }
});

// Sign out function
function signOut() {
    localStorage.removeItem('codeSageAuth');
    myinformation.authenticated = false;
    myinformation.username = "";
    myinformation.password = "";
    updateAuthSection();
    // Redirect to home page
    Enterpage('../Home');
}

// Tab functionality
function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tabcontent').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show the selected tab content
    document.getElementById(tabName).classList.add('active');
    
    // Update active tab button
    document.querySelectorAll('.tabbutton').forEach(button => {
        button.classList.remove('active');
    });
    
    event.target.classList.add('active');
}

// Initialize pages
function initPage() {
    checkAuthStatus();
    
    // Set up tab functionality if on problems page
    if (document.querySelector('.tabsnavigation')) {
        document.querySelector('.tabbutton').classList.add('active');
        document.querySelector('.tabcontent').classList.add('active');
    }
}

// Run initialization when DOM is loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPage);
} else {
    initPage();
}