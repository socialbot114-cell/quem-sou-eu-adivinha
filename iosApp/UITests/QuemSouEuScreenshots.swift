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
        internationalMusic.tap()
        XCTAssertTrue(app.buttons["Sim"].waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-jogo-musica-internacional")

        for _ in 0..<14 {
            let unknown = app.buttons["Não sei"]
            guard unknown.waitForExistence(timeout: 3) else { break }
            unknown.tap()
        }
        XCTAssertTrue(app.staticTexts["Quase!"].waitForExistence(timeout: 8))
        capture(app, name: "quem-sou-eu-resultado")

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
