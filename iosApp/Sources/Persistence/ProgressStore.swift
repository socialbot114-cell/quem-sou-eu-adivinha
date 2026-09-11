import Foundation

@MainActor final class ProgressStore: ObservableObject {
    @Published private(set) var points: Int
    @Published private(set) var coins: Int
    @Published private(set) var streak: Int
    @Published private(set) var wins: Int

    private let defaults = UserDefaults.standard
    init() {
        points = defaults.integer(forKey: "points")
        coins = defaults.integer(forKey: "coins")
        streak = defaults.integer(forKey: "streak")
        wins = defaults.integer(forKey: "wins")
    }
    func recordWin(questions: Int) {
        wins += 1; points += max(50, 150 - questions * 5); coins += 20; streak = max(streak, 1)
        defaults.set(points, forKey: "points"); defaults.set(coins, forKey: "coins"); defaults.set(streak, forKey: "streak"); defaults.set(wins, forKey: "wins")
    }
}
