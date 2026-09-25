import XCTest

final class QuemSouEuScreenshots: XCTestCase {
    func testCaptureStoreScreens() {
        let app = XCUIApplication()
        app.launchArguments = ["-onboarding.completed", "YES"]
        app.launch()

        if app.buttons["Pular"].waitForExistence(timeout: 2) {
            app.buttons["Pular"].tap()
        }

        XCTAssertTrue(app.buttons["home.play"].waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-home")

        let categoriesTab = app.buttons["tab.categories"]
        XCTAssertTrue(categoriesTab.waitForExistence(timeout: 8))
        categoriesTab.tap()
        XCTAssertTrue(app.buttons["category.all"].waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-categorias-inicio")

        let categoryScroll = app.scrollViews.firstMatch
        XCTAssertTrue(categoryScroll.waitForExistence(timeout: 4))
        categoryScroll.swipeUp()
        let internationalMusic = app.buttons["category.Música internacional"]
        XCTAssertTrue(internationalMusic.waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-categorias-expansao")
        let artists = app.buttons["category.Artistas brasileiros"]
        for _ in 0..<4 where !artists.isHittable {
            categoryScroll.swipeDown()
        }
        XCTAssertTrue(artists.isHittable)
        artists.tap()
        XCTAssertTrue(app.buttons["Sim"].waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-jogo-artistas-brasileiros")

        let targetAnswers = [
            "brazilian": "Sim",
            "alive": "Sim",
            "male": "Não",
            "born_before_1970": "Não",
            "born_before_1990": "Não",
            "football": "Não",
            "artist": "Sim",
            "creator": "Não",
            "politician": "Não",
            "historical": "Não",
            "singer": "Sim",
            "actor": "Sim",
            "presenter": "Sim",
            "writer": "Não",
            "instrumentalist": "Não",
            "director": "Não",
            "grammy_winner": "Não",
        ]

        for _ in 0..<14 {
            if app.staticTexts["Já tenho um palpite!"].exists { break }
            let activeAttribute = targetAnswers.keys.first { app.staticTexts["question.\($0)"].exists }
            guard let activeAttribute, let answer = targetAnswers[activeAttribute] else {
                XCTFail("Nenhuma pergunta mapeada para o personagem de screenshot apareceu")
                break
            }
            let answerButton = app.buttons[answer].firstMatch
            XCTAssertTrue(answerButton.waitForExistence(timeout: 4))
            answerButton.tap()
        }
        XCTAssertTrue(app.staticTexts["Já tenho um palpite!"].waitForExistence(timeout: 12))
        XCTAssertTrue(app.staticTexts["Anitta"].waitForExistence(timeout: 4))
        capture(app, name: "quem-sou-eu-palpite-anitta")
        let confirm = app.buttons["Acertou!"]
        XCTAssertTrue(confirm.waitForExistence(timeout: 4))
        confirm.tap()
        XCTAssertTrue(app.staticTexts["ACERTEI!"].waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-resultado-vitoria")

        let changeCategory = app.buttons["Escolher outra categoria"]
        XCTAssertTrue(changeCategory.waitForExistence(timeout: 5))
        changeCategory.tap()
        let profileTab = app.buttons["tab.profile"]
        XCTAssertTrue(profileTab.waitForExistence(timeout: 5))
        profileTab.tap()
        XCTAssertTrue(app.staticTexts["Perfil e ajustes"].waitForExistence(timeout: 5))
        capture(app, name: "quem-sou-eu-perfil")
    }

    private func capture(_ app: XCUIApplication, name: String) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
