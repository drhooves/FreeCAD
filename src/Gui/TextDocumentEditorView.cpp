#include "PreCompiled.h"

#include <boost/bind.hpp>
#include <QString>
#include <QMessageBox>

#include <App/TextDocument.h>
#include <Gui/Document.h>
#include <Gui/Application.h>
#include <Gui/TextDocumentEditorView.h>

using namespace Gui;

TextDocumentEditorView::TextDocumentEditorView(
		 App::TextDocument* textDocument, QPlainTextEdit* editor,
		 QWidget* parent)
	: MDIView(0, parent)
{
	this->editor = editor;
	setCentralWidget(editor);
	editObject(textDocument);
}

TextDocumentEditorView::~TextDocumentEditorView()
{
}

void TextDocumentEditorView::editObject(App::TextDocument* obj)
{
	if (obj != nullptr) {
		connect(getEditor()->document(), SIGNAL(modificationChanged(bool)),
				this, SLOT(setWindowModified(bool)));

		setWindowTitle(QString::fromLatin1(obj->Label.getValue())
				+ QString::fromLatin1("[*]"));
		setDocument(Application::Instance->getDocument(obj->getDocument()));
		getEditor()->setPlainText(QString::fromUtf8(obj->Text.getValue()));
		this->textDocument = obj;
	}
}

bool TextDocumentEditorView::onMsg(const char* msg, const char**)
{
    if (strcmp(msg,"Save") == 0) {
        saveToObject();
        return true;
    }
    return false;
}

bool TextDocumentEditorView::onHasMsg(const char* msg) const
{
    if (strcmp(msg,"Save") == 0)
        return getEditor()->document()->isModified();
    return false;
}

bool TextDocumentEditorView::canClose()
{
    if (!getEditor()->document()->isModified())
        return true;

    this->setFocus();

	QString question {
		tr("The document has been modified.\n"
		"Do you want to save your changes?")};
	auto reply = QMessageBox::question(
			this, tr("Unsaved document"), question,
			QMessageBox::Yes|QMessageBox::Default, QMessageBox::No,
			QMessageBox::Cancel|QMessageBox::Escape);
	if (reply == QMessageBox::Yes)
		saveToObject();
	return reply != QMessageBox::Cancel;
}

void TextDocumentEditorView::saveToObject()
{
	textDocument->Text.setValue(
			getEditor()->document()->toPlainText().toStdString());
	getEditor()->document()->setModified(false);
}

#include "moc_TextDocumentEditorView.cpp"
