import XCTest
@testable import QuemSouEu

final class ProgressStoreTests: XCTestCase {
    private var defaults: UserDefaults!
    private var calendar: Calendar!
    private var suiteName = ""

    override func setUp() {
        super.setUp()
        suiteName = "ProgressStoreTests.\(UUID().uuidString)"
        defaults = UserDefaults(suiteName: suiteName)!
        calendar = Calendar(identifier: .gregorian)
        calendar.timeZone = TimeZone(secondsFromGMT: 0)!
    }

    override func tearDown() {
        defaults.removePersistentDomain(forName: suiteName)
        defaults = nil
        calendar = nil
        suiteName = ""
        super.tearDown()
    }

    @MainActor
    func testOnlyCompletedGamesUpdateCountsAndStreak() {
        let store = ProgressStore(defaults: defaults, calendar: calendar)
        let firstDay = date(2026, 9, 10)

        store.recordPlayed(on: firstDay)
        XCTAssertEqual(store.completedGames, 0)
        XCTAssertEqual(store.streak, 0)

        store.recordWin(questions: 4, category: .football, discoveredPersonID: "person-1", on: firstDay)
        store.recordLoss(questions: 8, category: .history, on: date(2026, 9, 11))

        XCTAssertEqual(store.completedGames, 2)
        XCTAssertEqual(store.wins, 1)
        XCTAssertEqual(store.losses, 1)
        XCTAssertEqual(store.streak, 2)
        XCTAssertEqual(store.points, 130)
        XCTAssertEqual(store.coins, 20)
        XCTAssertEqual(store.lastCategory, .history)
        XCTAssertEqual(store.categoryHistory, [.football, .history])
        XCTAssertEqual(store.discoveredPersonIDs, ["person-1"])
    }

    @MainActor
    func testMultipleCompletionsOnSameDayOnlyAdvanceStreakOnce() {
        let store = ProgressStore(defaults: defaults, calendar: calendar)
        let day = date(2026, 9, 10)

        store.recordWin(questions: 3, category: .all, on: day)
        store.recordLoss(questions: 5, category: .all, on: day.addingTimeInterval(3_600))

        XCTAssertEqual(store.completedGames, 2)
        XCTAssertEqual(store.streak, 1)
    }

    @MainActor
    func testStateRoundTripsAndInterruptedRoundIsClearedOnCompletion() {
        let first = ProgressStore(defaults: defaults, calendar: calendar)
        let summary = InterruptedRoundSummary(
            category: .artists,
            questionsAnswered: 3,
            currentQuestionID: "question-4",
            bestGuessPersonID: "person-2",
            updatedAt: date(2026, 9, 10)
        )
        first.saveInterruptedRound(summary)
        first.markDiscovered(personID: "person-1")

        let restored = ProgressStore(defaults: defaults, calendar: calendar)
        XCTAssertEqual(restored.interruptedRound, summary)
        XCTAssertEqual(restored.lastCategory, .artists)
        XCTAssertEqual(restored.discoveredPersonIDs, ["person-1"])

        restored.recordLoss(questions: 4, category: .artists, on: date(2026, 9, 12))
        let completed = ProgressStore(defaults: defaults, calendar: calendar)
        XCTAssertNil(completed.interruptedRound)
        XCTAssertEqual(completed.gameHistory.count, 1)
        XCTAssertEqual(completed.gameHistory.first?.outcome, .loss)
    }

    @MainActor
    func testMigratesExistingScalarKeys() {
        defaults.set(900, forKey: "points")
        defaults.set(80, forKey: "coins")
        defaults.set(4, forKey: "streak")
        defaults.set(7, forKey: "wins")
        defaults.set(date(2026, 9, 9), forKey: "lastPlayed")

        let store = ProgressStore(defaults: defaults, calendar: calendar)

        XCTAssertEqual(store.points, 900)
        XCTAssertEqual(store.coins, 80)
        XCTAssertEqual(store.streak, 4)
        XCTAssertEqual(store.wins, 7)
        XCTAssertEqual(store.completedGames, 7)

        let restored = ProgressStore(defaults: defaults, calendar: calendar)
        XCTAssertEqual(restored.snapshot, store.snapshot)
    }

    private func date(_ year: Int, _ month: Int, _ day: Int) -> Date {
        calendar.date(from: DateComponents(year: year, month: month, day: day, hour: 12))!
    }
}
