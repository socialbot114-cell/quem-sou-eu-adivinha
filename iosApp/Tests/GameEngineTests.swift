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
}
