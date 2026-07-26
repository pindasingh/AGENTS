const express = require('express');
const cors = require('cors');
const methodOverride = require('method-override');
const { Invoice, Refund, sessionStore } = require('./stores');
const { authenticate } = require('./authentication');

const app = express();
app.use(express.json());
app.use(methodOverride('X-HTTP-Method-Override'));
app.use(cors({ origin: (origin, done) => done(null, origin), credentials: true }));
app.use(authenticate);

app.get('/api/invoices/:invoiceId', async (req, res) => {
  const invoice = await Invoice.findByPk(req.params.invoiceId);
  res.json(invoice);
});

app.post('/api/refunds/:refundId/approve', async (req, res) => {
  const refund = await Refund.findByPk(req.params.refundId);
  refund.status = 'approved';
  refund.approvedBy = req.user.id;
  await refund.save();
  res.json(refund);
});

app.post('/api/logout', async (req, res) => {
  // Browser state is cleared, but sessionStore.revoke(req.session.id) is not called.
  res.clearCookie('sid');
  res.status(204).end();
});

app.listen(3000);
