import Foundation

enum GameOutcome: String, Codable, Equatable {
    case win
    case loss
}

struct CompletedGameRecord: Codable, Equatable {
    let outcome: GameOutcome
    let category: Category?
    let questions: Int
    let pointsEarned: Int
    let coinsEarned: Int
    let discoveredPersonID: String?
    let completedAt: Date
}

struct InterruptedRoundSummary: Codable, Equatable {
    let category: Category
    let questionsAnswered: Int
    let currentQuestionID: String?
    let bestGuessPersonID: String?
    let answers: [RecordedAnswer]
    let rejectedPersonIDs: [String]
    let updatedAt: Date
    let knowledgeFingerprint: String?

    init(
        category: Category,
        questionsAnswered: Int,
        currentQuestionID: String? = nil,
        bestGuessPersonID: String? = nil,
        answers: [RecordedAnswer] = [],
        rejectedPersonIDs: [String] = [],
        updatedAt: Date = Date(),
        knowledgeFingerprint: String? = nil
    ) {
        self.category = category
        self.questionsAnswered = max(0, questionsAnswered)
        self.currentQuestionID = currentQuestionID
        self.bestGuessPersonID = bestGuessPersonID
        self.answers = answers
        self.rejectedPersonIDs = rejectedPersonIDs
        self.updatedAt = updatedAt
        self.knowledgeFingerprint = knowledgeFingerprint
    }

    private enum CodingKeys: String, CodingKey {
        case category, questionsAnswered, currentQuestionID, bestGuessPersonID, answers, rejectedPersonIDs, updatedAt, knowledgeFingerprint
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        category = try container.decode(Category.self, forKey: .category)
        questionsAnswered = try container.decode(Int.self, forKey: .questionsAnswered)
        currentQuestionID = try container.decodeIfPresent(String.self, forKey: .currentQuestionID)
        bestGuessPersonID = try container.decodeIfPresent(String.self, forKey: .bestGuessPersonID)
        answers = try container.decodeIfPresent([RecordedAnswer].self, forKey: .answers) ?? []
        rejectedPersonIDs = try container.decodeIfPresent([String].self, forKey: .rejectedPersonIDs) ?? []
        updatedAt = try container.decode(Date.self, forKey: .updatedAt)
        knowledgeFingerprint = try container.decodeIfPresent(String.self, forKey: .knowledgeFingerprint)
    }
}

struct RecordedAnswer: Codable, Equatable {
    let questionID: String
    let answer: Answer
}

struct ProgressSnapshot: Codable, Equatable {
    var points: Int
    var coins: Int
    var streak: Int
    var wins: Int
    var losses: Int
    var completedGames: Int
    var lastCompletedAt: Date?
    var lastCategory: Category?
    var categoryHistory: [Category]
    var discoveredPersonIDs: Set<String>
    var interruptedRound: InterruptedRoundSummary?
    var gameHistory: [CompletedGameRecord]

    init(
        points: Int = 0,
        coins: Int = 0,
        streak: Int = 0,
        wins: Int = 0,
        losses: Int = 0,
        completedGames: Int = 0,
        lastCompletedAt: Date? = nil,
        lastCategory: Category? = nil,
        categoryHistory: [Category] = [],
        discoveredPersonIDs: Set<String> = [],
        interruptedRound: InterruptedRoundSummary? = nil,
        gameHistory: [CompletedGameRecord] = []
    ) {
        self.points = points
        self.coins = coins
        self.streak = streak
        self.wins = wins
        self.losses = losses
        self.completedGames = completedGames
        self.lastCompletedAt = lastCompletedAt
        self.lastCategory = lastCategory
        self.categoryHistory = categoryHistory
        self.discoveredPersonIDs = discoveredPersonIDs
        self.interruptedRound = interruptedRound
        self.gameHistory = gameHistory
    }

    private enum CodingKeys: String, CodingKey {
        case points, coins, streak, wins, losses, completedGames, lastCompletedAt
        case lastCategory, categoryHistory, discoveredPersonIDs, interruptedRound, gameHistory
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        points = try container.decodeIfPresent(Int.self, forKey: .points) ?? 0
        coins = try container.decodeIfPresent(Int.self, forKey: .coins) ?? 0
        streak = try container.decodeIfPresent(Int.self, forKey: .streak) ?? 0
        wins = try container.decodeIfPresent(Int.self, forKey: .wins) ?? 0
        losses = try container.decodeIfPresent(Int.self, forKey: .losses) ?? 0
        completedGames = try container.decodeIfPresent(Int.self, forKey: .completedGames) ?? wins + losses
        lastCompletedAt = try container.decodeIfPresent(Date.self, forKey: .lastCompletedAt)
        lastCategory = try container.decodeIfPresent(Category.self, forKey: .lastCategory)
        categoryHistory = try container.decodeIfPresent([Category].self, forKey: .categoryHistory) ?? []
        discoveredPersonIDs = try container.decodeIfPresent(Set<String>.self, forKey: .discoveredPersonIDs) ?? []
        interruptedRound = try container.decodeIfPresent(InterruptedRoundSummary.self, forKey: .interruptedRound)
        gameHistory = try container.decodeIfPresent([CompletedGameRecord].self, forKey: .gameHistory) ?? []
    }
}
