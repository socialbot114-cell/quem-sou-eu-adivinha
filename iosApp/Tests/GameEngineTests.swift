import XCTest
@testable import QuemSouEu

final class GameEngineTests: XCTestCase {
    func testEngineUpdatesConfidenceAndAvoidsRepeatedQuestions() {
        let people = [Person(id: "a", name: "A", categories: [.all], country: "BR", profession: "Teste", attributes: ["x": 1], avatarSymbol: "star.fill"), Person(id: "b", name: "B", categories: [.all], country: "BR", profession: "Teste", attributes: ["x": 0], avatarSymbol: "star.fill")]
        let question = Question(id: "x", text: "É?", attribute: "x", categories: [.all])
        var engine = GameEngine(people: people, questions: [question])
        XCTAssertEqual(engine.nextQuestion()?.id, "x")
        engine.apply(.yes, to: question)
        XCTAssertEqual(engine.bestGuess?.id, "a")
        XCTAssertNil(engine.nextQuestion())
    }
}
