import XCTest
@testable import QuemSouEu

final class GameEngineTests: XCTestCase {
    private let people = [
        Person(id: "a", name: "A", categories: [.all], country: "BR", profession: "Teste", attributes: ["x": 1, "y": 0], avatarSymbol: "star.fill"),
        Person(id: "b", name: "B", categories: [.all], country: "BR", profession: "Teste", attributes: ["x": 0, "y": 1], avatarSymbol: "star.fill"),
        Person(id: "c", name: "C", categories: [.all], country: "BR", profession: "Teste", attributes: ["x": 0, "y": 0], avatarSymbol: "star.fill")
    ]

    func testCharacterExpansionLoadsIntoTheOfflineKnowledgeBase() {
        let store = KnowledgeStore.shared
        XCTAssertNil(store.loadError)
        XCTAssertTrue(store.base.people.contains { $0.id == "jungkook" })
        XCTAssertTrue(store.base.people.contains { $0.id == "djavan" })
        XCTAssertTrue(store.base.questions.contains { $0.attribute == "basketball" })
        XCTAssertTrue(store.base.people.contains { $0.categories.contains(.technology) })
    }

    func testEngineSelectsDiscriminativeQuestionAndAvoidsRepeatedAttributes() {
        let questions = [
            Question(id: "x-one", text: "X?", attribute: "x", categories: [.all]),
            Question(id: "x-two", text: "Outro X?", attribute: "x", categories: [.all]),
            Question(id: "y", text: "Y?", attribute: "y", categories: [.all])
        ]
        var engine = GameEngine(people: people, questions: questions, randomIndex: { _ in 0 })

        let first = try! XCTUnwrap(engine.nextQuestion())
        engine.apply(.yes, to: first)
        let second = try! XCTUnwrap(engine.nextQuestion())

        XCTAssertNotEqual(first.attribute, second.attribute)
        XCTAssertEqual(engine.bestGuess?.id, "a")
    }

    func testUnknownAnswerDoesNotChangeScores() {
        let question = Question(id: "x", text: "X?", attribute: "x", categories: [.all])
        var engine = GameEngine(people: people, questions: [question], randomIndex: { _ in 0 })
        let before = engine.scores
        engine.apply(.unknown, to: question)
        XCTAssertEqual(engine.scores, before)
    }

    func testMissingAttributeDoesNotGainEvidence() {
        let withMissing = [
            Person(id: "a", name: "A", categories: [.all], country: "BR", profession: "Teste", attributes: ["x": 1], avatarSymbol: "star.fill"),
            Person(id: "b", name: "B", categories: [.all], country: "BR", profession: "Teste", attributes: [:], avatarSymbol: "star.fill")
        ]
        let question = Question(id: "x", text: "X?", attribute: "x", categories: [.all])
        var engine = GameEngine(people: withMissing, questions: [question], randomIndex: { _ in 0 })
        engine.apply(.yes, to: question)
        XCTAssertGreaterThan(engine.scores["a", default: 0], engine.scores["b", default: 0])
    }

    func testRejectingGuessRemovesItFromRanking() {
        let question = Question(id: "x", text: "X?", attribute: "x", categories: [.all])
        var engine = GameEngine(people: people, questions: [question], randomIndex: { _ in 0 })
        engine.apply(.yes, to: question)
        let guess = try! XCTUnwrap(engine.bestGuess)
        engine.reject(guess)
        XCTAssertNotEqual(engine.bestGuess?.id, guess.id)
    }

    func testRestoringAnswersRebuildsScoresAndSkipsAnsweredQuestion() {
        let questions = [
            Question(id: "x", text: "X?", attribute: "x", categories: [.all]),
            Question(id: "y", text: "Y?", attribute: "y", categories: [.all])
        ]
        var engine = GameEngine(people: people, questions: questions, randomIndex: { _ in 0 })

        engine.restore([RecordedAnswer(questionID: "x", answer: .yes)])

        XCTAssertEqual(engine.bestGuess?.id, "a")
        XCTAssertEqual(engine.nextQuestion()?.id, "y")
    }

    func testScoresSumToOneAfterApply() {
        let question = Question(id: "x", text: "X?", attribute: "x", categories: [.all])
        var engine = GameEngine(people: people, questions: [question], randomIndex: { _ in 0 })
        engine.apply(.yes, to: question)
        let total = engine.scores.values.reduce(0, +)
        XCTAssertEqual(total, 1.0, accuracy: 1e-6)
        XCTAssertTrue(engine.scores.values.allSatisfy { $0.isFinite && $0 >= 0 })
    }

    func testContradictoryAnswerKeepsTargetAlive() {
        let question = Question(id: "x", text: "X?", attribute: "x", categories: [.all])
        var engine = GameEngine(people: people, questions: [question], randomIndex: { _ in 0 })
        engine.apply(.no, to: question)
        XCTAssertGreaterThan(engine.scores["a", default: 0], 0)
    }

    func testInvalidRandomIndexFallback() {
        let question = Question(id: "x", text: "X?", attribute: "x", categories: [.all])
        var engine = GameEngine(people: people, questions: [question], randomIndex: { _ in 99 })
        XCTAssertNotNil(engine.nextQuestion())
    }

    func testRejectAllReturnsNilGuess() {
        var engine = GameEngine(people: people, questions: [], randomIndex: { _ in 0 })
        for person in people {
            engine.reject(person)
        }
        XCTAssertNil(engine.bestGuess)
        XCTAssertEqual(engine.confidence, 0)
    }

    func testSecondBestMarginRatioEntropy() {
        let question = Question(id: "x", text: "X?", attribute: "x", categories: [.all])
        var engine = GameEngine(people: people, questions: [question], randomIndex: { _ in 0 })
        engine.apply(.yes, to: question)
        XCTAssertEqual(engine.bestGuess?.id, "a")
        XCTAssertNotNil(engine.secondBest)
        XCTAssertGreaterThan(engine.margin, 0)
        XCTAssertGreaterThan(engine.ratio, 1.0)
        XCTAssertLessThanOrEqual(engine.effectiveCandidates, 3.0)
    }

    func testApplySameQuestionTwiceIsIdempotent() {
        let question = Question(id: "x", text: "X?", attribute: "x", categories: [.all])
        var engine = GameEngine(people: people, questions: [question], randomIndex: { _ in 0 })
        engine.apply(.yes, to: question)
        let afterFirst = engine.scores
        engine.apply(.yes, to: question)
        XCTAssertEqual(engine.scores, afterFirst)
    }

    func testUselessQuestionNeverSelected() {
        let useless = Question(id: "z", text: "Z?", attribute: "z", categories: [.all])
        let sameValuePeople = [
            Person(id: "a", name: "A", categories: [.all], country: "BR", profession: "Teste", attributes: ["z": 1], avatarSymbol: "star.fill"),
            Person(id: "b", name: "B", categories: [.all], country: "BR", profession: "Teste", attributes: ["z": 1], avatarSymbol: "star.fill")
        ]
        var engine = GameEngine(people: sameValuePeople, questions: [useless], randomIndex: { _ in 0 })
        XCTAssertNil(engine.nextQuestion())
    }

    func testNoRepeatedAttributeAcrossRounds() {
        let base = [
            Person(id: "a", name: "A", categories: [.all], country: "BR", profession: "Teste", attributes: ["p": 1, "q": 0, "r": 1, "s": 0], avatarSymbol: "star.fill"),
            Person(id: "b", name: "B", categories: [.all], country: "BR", profession: "Teste", attributes: ["p": 0, "q": 1, "r": 0, "s": 1], avatarSymbol: "star.fill")
        ]
        let questions = ["p", "q", "r", "s"].map {
            Question(id: $0, text: $0.uppercased(), attribute: $0, categories: [.all])
        }
        var engine = GameEngine(people: base, questions: questions, randomIndex: { _ in 0 })
        var seenAttributes: Set<String> = []
        var seenIDs: Set<String> = []
        while let question = engine.nextQuestion() {
            XCTAssertFalse(seenAttributes.contains(question.attribute), "Atributo repetido: \(question.attribute)")
            XCTAssertFalse(seenIDs.contains(question.id), "Pergunta repetida: \(question.id)")
            seenAttributes.insert(question.attribute)
            seenIDs.insert(question.id)
            engine.apply(.yes, to: question)
        }
        XCTAssertFalse(seenAttributes.isEmpty)
    }

    func testActualCatalogFindsAnittaWithTruthfulAnswers() {
        let result = playActualCatalogGame(targetID: "anitta", category: .artists)

        XCTAssertTrue(result.success)
        XCTAssertLessThanOrEqual(result.questions, GuessPolicy.questionLimit)
    }

    func testActualCatalogRecoversAfterContradictionAndRejectedGuess() {
        let result = playActualCatalogGame(
            targetID: "marilia-mendonca",
            category: .artists,
            contradictedInformativeAnswers: 1
        )

        XCTAssertNotEqual(result.firstGuessID, Optional("marilia-mendonca"))
        XCTAssertTrue(result.success)
        XCTAssertEqual(result.rejectedGuesses, 1)
        XCTAssertLessThanOrEqual(result.questions, GuessPolicy.questionLimit)
    }

    func testActualCatalogUsesExtraQuestionsAfterRejectedGuess() {
        // With the fixed 14-question limit this round was lost; the extra questions after a rejection recover it.
        let result = playActualCatalogGame(
            targetID: "lula",
            category: .politicians,
            contradictedInformativeAnswers: 2
        )

        XCTAssertTrue(result.success)
        XCTAssertGreaterThanOrEqual(result.rejectedGuesses, 1)
        XCTAssertGreaterThan(result.questions, GuessPolicy.questionLimit)
        XCTAssertLessThanOrEqual(result.questions, GuessPolicy.maximumQuestionLimit)
    }

    func testQuestionBudgetGrowsAfterRejectedGuessesAndUnknownAnswers() {
        XCTAssertEqual(GuessPolicy.questionBudget(availableAttributes: 100, rejectedGuesses: 0, unknownAnswers: 0), 14)
        XCTAssertEqual(GuessPolicy.questionBudget(availableAttributes: 100, rejectedGuesses: 1, unknownAnswers: 0), 17)
        XCTAssertEqual(GuessPolicy.questionBudget(availableAttributes: 100, rejectedGuesses: 0, unknownAnswers: 1), 15)
        XCTAssertEqual(GuessPolicy.questionBudget(availableAttributes: 100, rejectedGuesses: 0, unknownAnswers: 5), 16)
    }

    func testQuestionBudgetRespectsCaps() {
        XCTAssertEqual(GuessPolicy.questionBudget(availableAttributes: 100, rejectedGuesses: 3, unknownAnswers: 2), GuessPolicy.maximumQuestionLimit)
        XCTAssertEqual(GuessPolicy.questionBudget(availableAttributes: 9, rejectedGuesses: 2, unknownAnswers: 2), 9)
        XCTAssertEqual(GuessPolicy.questionBudget(availableAttributes: 0, rejectedGuesses: 0, unknownAnswers: 0), 0)
    }

    func testReplayingAnswersUndoesLastAnswerExactly() {
        let questions = [
            Question(id: "x", text: "X?", attribute: "x", categories: [.all]),
            Question(id: "y", text: "Y?", attribute: "y", categories: [.all])
        ]
        var reference = GameEngine(people: people, questions: questions, randomIndex: { _ in 0 })
        reference.apply(.yes, to: questions[0])
        reference.reject(people[0])

        var engine = GameEngine(people: people, questions: questions, randomIndex: { _ in 0 })
        engine.apply(.yes, to: questions[0])
        engine.reject(people[0])
        engine.apply(.no, to: questions[1])

        let undone = engine.replaying([RecordedAnswer(questionID: "x", answer: .yes)], rejectedPersonIDs: ["a"])

        for person in people {
            XCTAssertEqual(undone.scores[person.id, default: -1], reference.scores[person.id, default: -2], accuracy: 1e-12)
        }
        XCTAssertTrue(undone.rejectedPersonIDs.contains("a"))
        XCTAssertFalse(undone.asked.contains("y"))
    }

    func testMarkAskedPreventsQuestionFromBeingSelectedAgain() {
        let questions = [
            Question(id: "x", text: "X?", attribute: "x", categories: [.all]),
            Question(id: "y", text: "Y?", attribute: "y", categories: [.all])
        ]
        var engine = GameEngine(people: people, questions: questions, randomIndex: { _ in 0 })
        engine.markAsked(questions[0])
        XCTAssertEqual(engine.nextQuestion()?.id, "y")
        XCTAssertNil(engine.nextQuestion())
    }

    private func playActualCatalogGame(
        targetID: String,
        category: QuemSouEu.Category,
        contradictedInformativeAnswers: Int = 0
    ) -> (success: Bool, firstGuessID: String?, rejectedGuesses: Int, questions: Int) {
        let base = KnowledgeStore.shared.base
        guard let target = base.people.first(where: { $0.id == targetID }) else {
            XCTFail("Personagem não encontrado na base: \(targetID)")
            return (false, nil, 0, 0)
        }
        let people = category == .all
            ? base.people
            : base.people.filter { $0.categories.contains(category) }
        let questions = base.questions.filter {
            $0.categories.contains(.all) || $0.categories.contains(category) || category == .all
        }
        let availableAttributes = Set(questions.map(\.attribute)).count
        var engine = GameEngine(people: people, questions: questions, randomIndex: { _ in 0 })
        var questionCount = 0
        var unknownAnswers = 0
        var informativeAnswers = 0
        var rejectedGuesses = 0
        var firstGuessID: String?
        var questionLimit: Int {
            GuessPolicy.questionBudget(
                availableAttributes: availableAttributes,
                rejectedGuesses: rejectedGuesses,
                unknownAnswers: unknownAnswers
            )
        }

        while true {
            let question = questionCount < questionLimit ? engine.nextQuestion() : nil
            if let question {
                var answer = answer(for: target.attributes[question.attribute])
                if answer != .unknown {
                    informativeAnswers += 1
                    if informativeAnswers <= contradictedInformativeAnswers { answer = inverted(answer) }
                }
                if answer == .unknown { unknownAnswers += 1 }
                engine.apply(answer, to: question)
                questionCount += 1
            }

            let shouldGuess = question == nil
                || questionCount >= questionLimit
                || (
                    questionCount >= GuessPolicy.minimumAnswersBeforeGuess
                    && engine.confidence >= GuessPolicy.confidenceThreshold
                    && engine.margin >= GuessPolicy.marginThreshold
                )
            guard shouldGuess else { continue }

            guard let guess = engine.bestGuess, engine.confidence >= GuessPolicy.minimumGuessConfidence else {
                return (false, firstGuessID, rejectedGuesses, questionCount)
            }
            if firstGuessID == nil { firstGuessID = guess.id }
            if guess.id == targetID {
                return (true, firstGuessID, rejectedGuesses, questionCount)
            }

            engine.reject(guess)
            rejectedGuesses += 1
            if rejectedGuesses >= GuessPolicy.maximumRejectedGuesses
                || questionCount >= questionLimit
                || engine.bestGuess == nil {
                return (false, firstGuessID, rejectedGuesses, questionCount)
            }
        }
    }

    private func answer(for value: Double?) -> Answer {
        guard let value else { return .unknown }
        if value >= 0.875 { return .yes }
        if value >= 0.625 { return .probablyYes }
        if value >= 0.375 { return .unknown }
        if value >= 0.125 { return .probablyNo }
        return .no
    }

    private func inverted(_ answer: Answer) -> Answer {
        switch answer {
        case .yes: .no
        case .probablyYes: .probablyNo
        case .unknown: .unknown
        case .probablyNo: .probablyYes
        case .no: .yes
        }
    }
}
