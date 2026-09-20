import XCTest

final class QuemSouEuScreenshots: XCTestCase {
    func testCaptureStoreScreens() {
        let app = XCUIApplication()
        app.launchArguments = ["-onboarding.completed", "YES"]
        app.launch()

        if app.buttons["Pular"].waitForExistence(timeout: 2) {
            app.buttons["Pular"].tap()
        }

        if app.buttons["home.play"].waitForExistence(timeout: 4) {
            capture(app, name: "quem-sou-eu-home")
        }

        let categoriesTab = app.buttons["tab.categories"]
        if categoriesTab.waitForExistence(timeout: 4) {
            categoriesTab.tap()
            if app.buttons["category.all"].waitForExistence(timeout: 4) {
                capture(app, name: "quem-sou-eu-categorias")

                let firstCard = app.buttons.matching(NSPredicate(format: "identifier BEGINSWITH 'category.'")).element(boundBy: 0)
                if firstCard.waitForExistence(timeout: 2) {
                    firstCard.tap()
                    if app.buttons["Sim"].waitForExistence(timeout: 6) {
                        capture(app, name: "quem-sou-eu-jogo")
                    }
                }
            }
        }
    }

    private func capture(_ app: XCUIApplication, name: String) {
        let attachment = XCTAttachment(screenshot: app.screenshot())
        attachment.name = name
        attachment.lifetime = .keepAlways
        add(attachment)
    }
}
