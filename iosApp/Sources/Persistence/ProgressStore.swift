import Foundation
import Combine

@MainActor final class ProgressStore: ObservableObject {
    private enum Key {
        static let snapshot = "progress.snapshot.v1"
        static let points = "points"
        static let coins = "coins"
        static let streak = "streak"
        static let wins = "wins"
        static let losses = "losses"
        static let completedGames = "completedGames"
        static let lastPlayed = "lastPlayed"
        static let lastCategory = "lastCategory"
        static let categoryHistory = "categoryHistory"
        static let discoveredPersonIDs = "discoveredPersonIDs"
        static let interruptedRound = "interruptedRound"
    }

    @Published private var stored: ProgressSnapshot

    private let defaults: UserDefaults
    private let calendar: Calendar
    private let encoder = JSONEncoder()

    var snapshot: ProgressSnapshot { stored }
    var points: Int { stored.points }
    var coins: Int { stored.coins }
    var streak: Int { stored.streak }
    var wins: Int { stored.wins }
    var losses: Int { stored.losses }
    var completedGames: Int { stored.completedGames }
    var lastCategory: Category? { stored.lastCategory }
    var categoryHistory: [Category] { stored.categoryHistory }
    var discoveredPersonIDs: Set<String> { stored.discoveredPersonIDs }
    var interruptedRound: InterruptedRoundSummary? { stored.interruptedRound }
    var gameHistory: [CompletedGameRecord] { stored.gameHistory }

    init(defaults: UserDefaults = .standard, calendar: Calendar = .current) {
        self.defaults = defaults
        self.calendar = calendar
        stored = Self.load(from: defaults)
        persist(stored)
    }

    // Kept for the existing caller. Opening a game is not a completed play.
    func recordPlayed(on date: Date = Date()) {
        _ = date
    }

    func recordWin(questions: Int) {
        completeGame(outcome: .win, category: nil, questions: questions, discoveredPersonID: nil, on: Date())
    }

    func recordWin(
        questions: Int,
        category: Category,
        discoveredPersonID: String? = nil,
        on date: Date = Date()
    ) {
        completeGame(
            outcome: .win,
            category: category,
            questions: questions,
            discoveredPersonID: discoveredPersonID,
            on: date
        )
    }

    func recordLoss(
        questions: Int,
        category: Category,
        discoveredPersonID: String? = nil,
        on date: Date = Date()
    ) {
        completeGame(
            outcome: .loss,
            category: category,
            questions: questions,
            discoveredPersonID: discoveredPersonID,
            on: date
        )
    }

    func recordCompletedGame(
        outcome: GameOutcome,
        category: Category,
        questions: Int,
        discoveredPersonID: String? = nil,
        on date: Date = Date()
    ) {
        completeGame(
            outcome: outcome,
            category: category,
            questions: questions,
            discoveredPersonID: discoveredPersonID,
            on: date
        )
    }

    func markDiscovered(personID: String) {
        guard !personID.isEmpty else { return }
        update { progress in
            _ = progress.discoveredPersonIDs.insert(personID)
        }
    }

    func saveInterruptedRound(_ summary: InterruptedRoundSummary) {
        update {
            $0.interruptedRound = summary
            $0.lastCategory = summary.category
        }
    }

    func clearInterruptedRound() {
        guard stored.interruptedRound != nil else { return }
        update { $0.interruptedRound = nil }
    }

    private func completeGame(
        outcome: GameOutcome,
        category: Category?,
        questions: Int,
        discoveredPersonID: String?,
        on date: Date
    ) {
        let questionCount = max(0, questions)
        let pointsEarned = outcome == .win ? max(50, 150 - questionCount * 5) : 0
        let coinsEarned = outcome == .win ? 20 : 0

        update { progress in
            progress.completedGames += 1
            switch outcome {
            case .win:
                progress.wins += 1
            case .loss:
                progress.losses += 1
            }
            progress.points += pointsEarned
            progress.coins += coinsEarned
            updateStreak(in: &progress, completedAt: date)

            if let category {
                progress.lastCategory = category
                progress.categoryHistory.append(category)
            }
            if let discoveredPersonID, !discoveredPersonID.isEmpty {
                progress.discoveredPersonIDs.insert(discoveredPersonID)
            }
            progress.interruptedRound = nil
            progress.gameHistory.append(CompletedGameRecord(
                outcome: outcome,
                category: category,
                questions: questionCount,
                pointsEarned: pointsEarned,
                coinsEarned: coinsEarned,
                discoveredPersonID: discoveredPersonID,
                completedAt: date
            ))
            if progress.gameHistory.count > 100 {
                progress.gameHistory.removeFirst(progress.gameHistory.count - 100)
            }
        }
    }

    private func updateStreak(in progress: inout ProgressSnapshot, completedAt date: Date) {
        let completedDay = calendar.startOfDay(for: date)
        guard let previousDate = progress.lastCompletedAt else {
            progress.streak = 1
            progress.lastCompletedAt = completedDay
            return
        }

        let previousDay = calendar.startOfDay(for: previousDate)
        guard completedDay > previousDay else { return }
        let dayDifference = calendar.dateComponents([.day], from: previousDay, to: completedDay).day
        progress.streak = dayDifference == 1 ? progress.streak + 1 : 1
        progress.lastCompletedAt = completedDay
    }

    private func update(_ mutation: (inout ProgressSnapshot) -> Void) {
        var updated = stored
        mutation(&updated)
        stored = updated
        persist(updated)
    }

    private static func load(from defaults: UserDefaults) -> ProgressSnapshot {
        let decoder = JSONDecoder()
        if let data = defaults.data(forKey: Key.snapshot),
           var decoded = try? decoder.decode(ProgressSnapshot.self, from: data) {
            decoded.completedGames = max(decoded.completedGames, decoded.wins + decoded.losses)
            return decoded
        }

        let wins = defaults.integer(forKey: Key.wins)
        let losses = defaults.integer(forKey: Key.losses)
        let completedGames = defaults.object(forKey: Key.completedGames) == nil
            ? wins + losses
            : max(defaults.integer(forKey: Key.completedGames), wins + losses)
        let lastCategory = defaults.string(forKey: Key.lastCategory).flatMap { value in
            if value == "TikTok" || value == "Instagram" { return .creators }
            return Category(rawValue: value)
        }
        let categoryHistory = decode([Category].self, key: Key.categoryHistory, from: defaults) ?? []
        let discoveredIDs = Set(defaults.stringArray(forKey: Key.discoveredPersonIDs) ?? [])
        let interruptedRound = decode(InterruptedRoundSummary.self, key: Key.interruptedRound, from: defaults)

        return ProgressSnapshot(
            points: defaults.integer(forKey: Key.points),
            coins: defaults.integer(forKey: Key.coins),
            streak: defaults.integer(forKey: Key.streak),
            wins: wins,
            losses: losses,
            completedGames: completedGames,
            lastCompletedAt: defaults.object(forKey: Key.lastPlayed) as? Date,
            lastCategory: lastCategory,
            categoryHistory: categoryHistory,
            discoveredPersonIDs: discoveredIDs,
            interruptedRound: interruptedRound
        )
    }

    private static func decode<Value: Decodable>(
        _ type: Value.Type,
        key: String,
        from defaults: UserDefaults
    ) -> Value? {
        guard let data = defaults.data(forKey: key) else { return nil }
        return try? JSONDecoder().decode(type, from: data)
    }

    private func persist(_ progress: ProgressSnapshot) {
        if let data = try? encoder.encode(progress) {
            defaults.set(data, forKey: Key.snapshot)
        }

        // Mirror legacy keys to preserve compatibility with the previous store.
        defaults.set(progress.points, forKey: Key.points)
        defaults.set(progress.coins, forKey: Key.coins)
        defaults.set(progress.streak, forKey: Key.streak)
        defaults.set(progress.wins, forKey: Key.wins)
        defaults.set(progress.losses, forKey: Key.losses)
        defaults.set(progress.completedGames, forKey: Key.completedGames)
        if let lastCompletedAt = progress.lastCompletedAt {
            defaults.set(lastCompletedAt, forKey: Key.lastPlayed)
        } else {
            defaults.removeObject(forKey: Key.lastPlayed)
        }
        if let lastCategory = progress.lastCategory {
            defaults.set(lastCategory.rawValue, forKey: Key.lastCategory)
        } else {
            defaults.removeObject(forKey: Key.lastCategory)
        }
        defaults.set(progress.discoveredPersonIDs.sorted(), forKey: Key.discoveredPersonIDs)

        persist(progress.categoryHistory, key: Key.categoryHistory)
        if let interruptedRound = progress.interruptedRound {
            persist(interruptedRound, key: Key.interruptedRound)
        } else {
            defaults.removeObject(forKey: Key.interruptedRound)
        }
    }

    private func persist<Value: Encodable>(_ value: Value, key: String) {
        if let data = try? encoder.encode(value) {
            defaults.set(data, forKey: key)
        }
    }
}
