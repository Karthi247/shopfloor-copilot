import React from 'react';
import Icon from './Icon';

const suggestedQuestions = [
  'How do I handle CNC machine alarms?',
  'What is the incoming material inspection process?',
  'Explain the Lockout / Tagout procedure.',
  'What are the TX-200 preventive maintenance requirements?',
];

const quickActions = [
  {
    icon: 'maintenance',
    title: 'CNC machine alarms',
    question:
      'The machine is showing alarm AL-104. What does it mean and what should the operator do?',
  },
  {
    icon: 'maintenance',
    title: 'Preventive maintenance',
    question: 'What preventive maintenance steps are listed for the TX-200 CNC?',
  },
  {
    icon: 'quality',
    title: 'Incoming inspection',
    question: 'What are the current incoming material inspection requirements?',
  },
  {
    icon: 'safety',
    title: 'Lockout / Tagout',
    question:
      'What does the lockout/tagout procedure require before maintenance begins?',
  },
  {
    icon: 'quality',
    title: 'BH-220 inspection',
    question: 'What is the outer diameter tolerance for the BH-220 part?',
  },
];

export default function WelcomeScreen({ onAsk, composer }) {
  return (
    <div className="welcome-screen">
      <div className="welcome-content">
        <div className="welcome-emblem">
          <Icon name="spark" size={23} />
        </div>
        <div className="welcome-eyebrow">SHOPFLOOR KNOWLEDGE</div>
        <h2>Your ShopFloor Knowledge Assistant</h2>
        <p>
          Find reliable answers from your manufacturing SOPs, maintenance manuals and
          safety procedures.
        </p>
        {composer && <div className="welcome-composer">{composer}</div>}
        <div className="suggested-questions" aria-label="Suggested questions">
          {suggestedQuestions.map((question) => (
            <button key={question} onClick={() => onAsk(question)}>
              <span>{question}</span>
              <Icon name="send" size={15} />
            </button>
          ))}
        </div>
      </div>
      <section className="quick-actions-section">
        <div className="quick-actions-heading">
          <div>
            <span className="section-kicker">SHIFT QUICK ACTIONS</span>
            <h3>Common shop-floor questions</h3>
          </div>
          <span className="quick-actions-note">
            Answers grounded in indexed procedures
          </span>
        </div>
        <div className="quick-actions-grid">
          {quickActions.map((action) => (
            <button
              className="quick-action-card"
              key={action.title}
              onClick={() => onAsk(action.question)}
            >
              <span className={`quick-action-icon ${action.icon}`}>
                <Icon name={action.icon} size={17} />
              </span>
              <span className="quick-action-copy">
                <strong>{action.title}</strong>
                <small>{action.question}</small>
              </span>
              <Icon name="send" size={14} className="quick-action-arrow" />
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
