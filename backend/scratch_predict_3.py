import requests

def analyze():
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    for sym in symbols:
        try:
            print(f"--- Analyzing {sym} ---")
            # Fetch Daily Prediction
            url = f"http://127.0.0.1:8001/api/v1/prediction/daily/{sym}"
            r = requests.get(url)
            if r.status_code == 200:
                data = r.json().get("data", {})
                pred = data.get("prediction", {})
                ml = data.get("ml_model", {})
                
                print("Daily Prediction:")
                print(f"  Direction: {pred.get('direction')}")
                print(f"  Final Score: {pred.get('final_score')}")
                print(f"  ML Status: {ml.get('status')} (Accuracy: {ml.get('test_accuracy_pct')}%)")
                print(f"  ML Prediction: {ml.get('prediction', {}).get('predicted_direction')} (Prob: {ml.get('prediction', {}).get('probability_up')})")
                print(f"  News Sentiment: {data.get('fundamental', {}).get('news_sentiment')}")
                print(f"  Latest Catalyst: {data.get('fundamental', {}).get('latest_catalyst')}")
            else:
                print(f"Failed to fetch Daily for {sym}: {r.status_code}")

            # Fetch 3-Hour Prediction
            url3h = f"http://127.0.0.1:8001/api/v1/prediction/three-hours/{sym}"
            r3h = requests.get(url3h)
            if r3h.status_code == 200:
                d3 = r3h.json().get("data", {})
                outlook = d3.get("outlook_summary", {})
                print("3-Hour Outlook:")
                print(f"  Direction: {outlook.get('overall_direction')}")
                print(f"  Conviction: {outlook.get('conviction_strength')} / 100")
                print(f"  Tactic: {outlook.get('tactical_strategy')}")
                print(f"  Target Peak: {outlook.get('target_peak')}")
            else:
                print(f"Failed to fetch 3H for {sym}: {r3h.status_code}")
                
            print("\n")
        except Exception as e:
            print(f"Error on {sym}: {e}")

if __name__ == "__main__":
    analyze()
