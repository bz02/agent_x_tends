using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;
using TMPro;

namespace VoiceSupport
{
    [Serializable]
    public class UserNeedingSupport
    {
        public string username;
        public string user_id;
        public string profile_url;
        public string original_post;
        public string post_url;
        public SentimentAnalysis sentiment_analysis;
        public string support_message;
        public ContactInfo contact_info;
        public string timestamp;
    }

    [Serializable]
    public class SentimentAnalysis
    {
        public bool is_negative;
        public string sentiment;
        public string severity;
        public string[] concerns;
        public bool needs_support;
        public string reasoning;
    }

    [Serializable]
    public class ContactInfo
    {
        public string username;
        public string name;
        public string description;
        public string location;
        public string url;
        public string profile_url;
    }

    [Serializable]
    public class UsersResponse
    {
        public UserNeedingSupport[] users;
        public string scan_timestamp;
        public int total_found;
    }

    [Serializable]
    public class CallRequest
    {
        public string user_id;
        public string username;
        public string phone_number;
        public Dictionary<string, object> context;
    }

    [Serializable]
    public class CallResponse
    {
        public string conversation_id;
        public string call_id;
        public string phone_number;
        public string initial_message;
        public string status;
    }

    [Serializable]
    public class ConversationMessage
    {
        public string role;
        public string content;
        public string timestamp;
    }

    [Serializable]
    public class ConversationResponse
    {
        public string user_id;
        public Dictionary<string, object> memory;
        public ConversationMessage[] conversations;
        public int total_messages;
    }

    public class SupportCallManager : MonoBehaviour
    {
        [Header("API Configuration")]
        public string backendUrl = "http://localhost:8001";
        public string telephonyUrl = "http://localhost:3000";

        [Header("UI References")]
        public Transform userListContainer;
        public GameObject userItemPrefab;
        public TextMeshProUGUI statusText;
        public Button refreshButton;
        public Button callButton;
        public InputField phoneNumberInput;
        public TextMeshProUGUI conversationText;
        public ScrollRect conversationScrollRect;

        private List<UserNeedingSupport> currentUsers = new List<UserNeedingSupport>();
        private UserNeedingSupport selectedUser;
        private List<ConversationMessage> conversationHistory = new List<ConversationMessage>();

        void Start()
        {
            if (refreshButton != null)
                refreshButton.onClick.AddListener(LoadUsersNeedingSupport);
            
            if (callButton != null)
                callButton.onClick.AddListener(InitiateCall);

            LoadUsersNeedingSupport();
        }

        public void LoadUsersNeedingSupport()
        {
            StartCoroutine(LoadUsersCoroutine());
        }

        IEnumerator LoadUsersCoroutine()
        {
            UpdateStatus("Loading users needing support...");

            string url = $"{backendUrl}/api/users/needing-support";
            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        // Parse the response - it should have a "users" array
                        string jsonText = request.downloadHandler.text;
                        // If the response is just an array, wrap it
                        if (jsonText.TrimStart().StartsWith("["))
                        {
                            jsonText = "{\"users\":" + jsonText + "}";
                        }
                        UsersResponse response = JsonUtility.FromJson<UsersResponse>(jsonText);
                        
                        currentUsers = new List<UserNeedingSupport>(response.users);
                        UpdateUserList();
                        UpdateStatus($"Loaded {currentUsers.Count} users needing support");
                    }
                    catch (Exception e)
                    {
                        UpdateStatus($"Error parsing response: {e.Message}");
                        Debug.LogError($"Parse error: {e}");
                    }
                }
                else
                {
                    UpdateStatus($"Error: {request.error}");
                    Debug.LogError($"Request error: {request.error}");
                }
            }
        }

        void UpdateUserList()
        {
            // Clear existing items
            foreach (Transform child in userListContainer)
            {
                Destroy(child.gameObject);
            }

            // Create items for each user
            foreach (var user in currentUsers)
            {
                GameObject item = Instantiate(userItemPrefab, userListContainer);
                
                // Set up user item UI
                var userItemScript = item.GetComponent<UserListItem>();
                if (userItemScript != null)
                {
                    userItemScript.SetUser(user, this);
                }
                else
                {
                    // Fallback: set text directly
                    var text = item.GetComponentInChildren<TextMeshProUGUI>();
                    if (text != null)
                    {
                        text.text = $"@{user.username}\n{user.original_post.Substring(0, Mathf.Min(50, user.original_post.Length))}...";
                    }
                }
            }
        }

        public void SelectUser(UserNeedingSupport user)
        {
            selectedUser = user;
            LoadConversationHistory(user.user_id);
            UpdateStatus($"Selected: @{user.username}");
        }

        void LoadConversationHistory(string userId)
        {
            StartCoroutine(LoadConversationCoroutine(userId));
        }

        IEnumerator LoadConversationCoroutine(string userId)
        {
            string url = $"{backendUrl}/api/conversations/{userId}";
            using (UnityWebRequest request = UnityWebRequest.Get(url))
            {
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        ConversationResponse response = JsonUtility.FromJson<ConversationResponse>(
                            request.downloadHandler.text
                        );
                        
                        conversationHistory.Clear();
                        if (response.conversations != null)
                        {
                            conversationHistory.AddRange(response.conversations);
                        }
                        
                        UpdateConversationDisplay();
                    }
                    catch (Exception e)
                    {
                        Debug.LogError($"Error parsing conversation: {e}");
                    }
                }
            }
        }

        void UpdateConversationDisplay()
        {
            if (conversationText == null) return;

            string displayText = "";
            foreach (var msg in conversationHistory)
            {
                string roleLabel = msg.role == "user" ? "User" : "Assistant";
                displayText += $"[{roleLabel}] {msg.content}\n\n";
            }

            conversationText.text = displayText;

            // Scroll to bottom
            if (conversationScrollRect != null)
            {
                Canvas.ForceUpdateCanvases();
                conversationScrollRect.verticalNormalizedPosition = 0f;
            }
        }

        public void InitiateCall()
        {
            if (selectedUser == null)
            {
                UpdateStatus("Please select a user first");
                return;
            }

            string phoneNumber = phoneNumberInput != null ? phoneNumberInput.text : "";
            if (string.IsNullOrEmpty(phoneNumber))
            {
                UpdateStatus("Please enter a phone number");
                return;
            }

            StartCoroutine(InitiateCallCoroutine());
        }

        IEnumerator InitiateCallCoroutine()
        {
            UpdateStatus("Initiating call...");

            CallRequest request = new CallRequest
            {
                user_id = selectedUser.user_id,
                username = selectedUser.username,
                phone_number = phoneNumberInput != null ? phoneNumberInput.text : "",
                context = new Dictionary<string, object>
                {
                    { "original_post", selectedUser.original_post },
                    { "sentiment_analysis", selectedUser.sentiment_analysis },
                    { "support_message", selectedUser.support_message }
                }
            };

            string json = JsonUtility.ToJson(request);
            string url = $"{telephonyUrl}/api/calls/initiate";

            using (UnityWebRequest webRequest = new UnityWebRequest(url, "POST"))
            {
                byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
                webRequest.uploadHandler = new UploadHandlerRaw(bodyRaw);
                webRequest.downloadHandler = new DownloadHandlerBuffer();
                webRequest.SetRequestHeader("Content-Type", "application/json");

                yield return webRequest.SendWebRequest();

                if (webRequest.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        CallResponse response = JsonUtility.FromJson<CallResponse>(
                            webRequest.downloadHandler.text
                        );
                        
                        UpdateStatus($"Call initiated! Conversation ID: {response.conversation_id}");
                        
                        // Add initial message to conversation
                        conversationHistory.Add(new ConversationMessage
                        {
                            role = "assistant",
                            content = response.initial_message,
                            timestamp = DateTime.Now.ToString("o")
                        });
                        UpdateConversationDisplay();
                    }
                    catch (Exception e)
                    {
                        UpdateStatus($"Error parsing response: {e.Message}");
                    }
                }
                else
                {
                    UpdateStatus($"Error: {webRequest.error}");
                }
            }
        }

        void UpdateStatus(string message)
        {
            if (statusText != null)
            {
                statusText.text = $"[{DateTime.Now:HH:mm:ss}] {message}";
            }
            Debug.Log(message);
        }
    }
}

