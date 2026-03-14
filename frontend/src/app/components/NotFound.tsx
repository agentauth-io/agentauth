import { useNavigate } from "react-router-dom";

export function NotFound() {
  const navigate = useNavigate();

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#08080a",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        color: "#fff",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h1
        style={{
          fontSize: "8rem",
          fontWeight: 700,
          margin: 0,
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}
      >
        404
      </h1>
      <h2
        style={{
          fontSize: "1.5rem",
          fontWeight: 400,
          color: "#888",
          marginTop: "1rem",
        }}
      >
        Page Not Found
      </h2>
      <p
        style={{
          color: "#666",
          marginTop: "0.5rem",
          maxWidth: "400px",
          textAlign: "center",
        }}
      >
        The page you're looking for doesn't exist or has been moved.
      </p>
      <button
        onClick={() => navigate("/")}
        style={{
          marginTop: "2rem",
          padding: "0.75rem 2rem",
          fontSize: "1rem",
          fontWeight: 500,
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          border: "none",
          borderRadius: "8px",
          color: "#fff",
          cursor: "pointer",
          transition: "transform 0.2s, opacity 0.2s",
        }}
        onMouseOver={(e) => (e.currentTarget.style.opacity = "0.9")}
        onMouseOut={(e) => (e.currentTarget.style.opacity = "1")}
      >
        Go Home
      </button>
    </div>
  );
}
