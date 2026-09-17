import Foundation

@MainActor final class ProgressStore: ObservableObject {
    @Published private(set) var points: Int
    @Published private(set) var coins: Int
    @Published private(set) var streak: Int
    @Published private(set) var wins: Int

    private let defaults = UserDefaults.standard
    private let calendar = Calendar.current
    init() {
        points = defaults.integer(forKey: "points")
        coins = defaults.integer(forKey: "coins")
        streak = defaults.integer(forKey: "streak")
        wins = defaults.integer(forKey: "wins")
    }
    func recordPlayed(on date: Date = Date()) {
        let today = calendar.startOfDay(for: date)
        let lastPlayed = defaults.object(forKey: "lastPlayed") as? Date
        if let lastPlayed, calendar.isDate(lastPlayed, inSameDayAs: today) { return }
        if let lastPlayed, let yesterday = calendar.date(byAdding: .day, value: -1, to: today), calendar.isDate(lastPlayed, inSameDayAs: yesterday) {
            streak += 1
        } else {
            streak = 1
        }
        defaults.set(today, forKey: "lastPlayed")
        defaults.set(streak, forKey: "streak")
    }
    func recordWin(questions: Int) {
        wins += 1
        points += max(50, 150 - questions * 5)
        coins += 20
        defaults.set(points, forKey: "points")
        defaults.set(coins, forKey: "coins")
        defaults.set(wins, forKey: "wins")
    }
}
