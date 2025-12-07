using UnityEngine;
using UnityEngine.UI;
using TMPro;

namespace VoiceSupport
{
    public class UserListItem : MonoBehaviour
    {
        public TextMeshProUGUI usernameText;
        public TextMeshProUGUI postText;
        public TextMeshProUGUI sentimentText;
        public Button selectButton;

        private UserNeedingSupport user;
        private SupportCallManager manager;

        void Start()
        {
            if (selectButton != null)
            {
                selectButton.onClick.AddListener(OnSelect);
            }
        }

        public void SetUser(UserNeedingSupport user, SupportCallManager manager)
        {
            this.user = user;
            this.manager = manager;

            if (usernameText != null)
            {
                usernameText.text = $"@{user.username}";
            }

            if (postText != null)
            {
                string postPreview = user.original_post.Length > 100 
                    ? user.original_post.Substring(0, 100) + "..." 
                    : user.original_post;
                postText.text = postPreview;
            }

            if (sentimentText != null && user.sentiment_analysis != null)
            {
                string severity = user.sentiment_analysis.severity ?? "unknown";
                string sentiment = user.sentiment_analysis.sentiment ?? "unknown";
                sentimentText.text = $"{sentiment.ToUpper()} - {severity.ToUpper()}";
                
                // Color code by severity
                Color color = severity.ToLower() switch
                {
                    "high" => Color.red,
                    "medium" => new Color(1f, 0.5f, 0f), // Orange
                    "low" => Color.yellow,
                    _ => Color.white
                };
                sentimentText.color = color;
            }
        }

        void OnSelect()
        {
            if (manager != null && user != null)
            {
                manager.SelectUser(user);
            }
        }
    }
}

