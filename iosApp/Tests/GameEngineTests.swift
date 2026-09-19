import XCTest
@testable import QuemSouEu

final class GameEngineTests: XCTestCase {
    private let people = [
        Person(id: "a", name: "A", categories: [.all], country: "BR", profession: "Teste", attributes: ["x": 1, "y": 0], avatarSymbol: "star.fill"),
        Person(id: "b", name: "B", categories: [.all], country: "BR", profession: "Teste", attributes: ["x": 0, "y": 1], avatarSymbol: "star.fill"),
        Person(id: "c", name: "C", categories: [.all], country: "BR", profession: "Teste", attributes: ["x": 0, "y": 0], avatarSymbol: "star.fill")
    ]

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
}
