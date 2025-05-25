import VoicenovelLogo from './voicenovel_logo.png'; 

<style jsx>{`
  .main-bg {
    min-height: 100vh;
    background: #fff;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .nav-bar {
    width: 100%;
    max-width: 1920px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 32px 48px 0 48px;
  }
  .nav-logo img {
    height: 60px;
  }
  .nav-items {
    display: flex;
    gap: 36px;
  }
  .nav-link {
    color: #0c4270;
    font-family: 'Urbanist', sans-serif;
    font-weight: 700;
    font-size: 16px;
    text-decoration: none;
    transition: color 0.2s;
  }
  .nav-link:hover {
    color: #535bf2;
  }
  .nav-login .login-btn {
    background: #0c4270;
    color: #c9c9c9;
    border: none;
    border-radius: 20px;
    padding: 10px 28px;
    font-size: 16px;
    font-family: 'Urbanist', sans-serif;
    font-weight: 700;
    cursor: pointer;
  }
  .main-logo-container {
    margin: 60px 0 20px 0;
    display: flex;
    justify-content: center;
  }
  .main-logo {
    width: 825px;
    height: 575px;
    object-fit: contain;
  }
  .main-desc-section {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-top: 40px;
  }
  .main-desc-title {
    font-family: 'Gowun Batang', serif;
    font-size: 28px;
    color: #0c4270;
    text-align: center;
    margin-bottom: 20px;
  }
  .get-started-btn {
    background: #0c4270;
    color: #fff;
    border: none;
    border-radius: 220px;
    padding: 10px 32px;
    font-size: 15px;
    font-family: 'Urbanist', sans-serif;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(12, 66, 112, 0.08);
  }
  .arrow-icon {
    font-size: 20px;
    margin-left: 8px;
  }
  @media (max-width: 900px) {
    .main-logo {
      width: 300px;
      height: 180px;
    }
    .main-desc-title {
      font-size: 18px;
    }
  }
`}</style> 